"""Authoritative refund eligibility policy. No I/O or implicit clock."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


REFUND_WINDOW = timedelta(days=30)
REFUNDABLE_STATES = frozenset({"paid", "shipped"})


class RefundError(ValueError):
    """A request violates a documented refund contract."""


class Ineligible(RefundError):
    pass


class RequestConflict(RefundError):
    """An idempotency key belongs to a different order."""


class AlreadyRequested(RefundError):
    """A different key has already requested this order's full refund."""


def require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")


@dataclass(frozen=True)
class Order:
    order_id: str
    paid_at: datetime
    amount_cents: int
    state: str = "paid"

    def __post_init__(self) -> None:
        require_aware(self.paid_at)
        if not self.order_id:
            raise ValueError("order_id must not be empty")
        if type(self.amount_cents) is not int or self.amount_cents <= 0:
            raise ValueError("amount_cents must be a positive integer")


@dataclass(frozen=True)
class RefundRequest:
    request_id: str
    order_id: str
    amount_cents: int
    requested_at: datetime

    def __post_init__(self) -> None:
        require_aware(self.requested_at)
        if not self.request_id or not self.order_id:
            raise ValueError("request and order IDs must not be empty")
        if type(self.amount_cents) is not int or self.amount_cents <= 0:
            raise ValueError("amount_cents must be a positive integer")


def approve(order: Order, now: datetime, request_id: str) -> RefundRequest:
    """Approve one full refund request in the first 30 elapsed 24-hour days.

    Idempotency and uniqueness are ledger responsibilities; this function has no
    knowledge of prior requests. A returned request does not mean money moved.
    """
    require_aware(now)
    if order.state not in REFUNDABLE_STATES:
        raise Ineligible("order state is not refundable")
    elapsed = now.astimezone(timezone.utc) - order.paid_at.astimezone(timezone.utc)
    if not timedelta(0) <= elapsed < REFUND_WINDOW:
        raise Ineligible("outside refund window")
    return RefundRequest(request_id, order.order_id, order.amount_cents, now)
