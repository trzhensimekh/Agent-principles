"""In-memory stock reservations for single-threaded use."""

from collections.abc import Callable
from dataclasses import dataclass, replace
import math
import time

__all__ = ["Inventory", "OutOfStock", "Conflict"]


class OutOfStock(ValueError):
    """The requested quantity exceeds the available stock."""


class Conflict(ValueError):
    """A request ID was previously used with different reservation details."""


def _validate_identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")


def _validate_quantity(quantity: int) -> None:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("quantity must be a positive integer, not bool")


def _validate_ttl(ttl_seconds: int | float) -> None:
    if (
        isinstance(ttl_seconds, bool)
        or not isinstance(ttl_seconds, (int, float))
        or ttl_seconds <= 0
        or (isinstance(ttl_seconds, float) and not math.isfinite(ttl_seconds))
    ):
        raise ValueError("ttl_seconds must be a positive finite int or float, not bool")


@dataclass(frozen=True, slots=True)
class _Reservation:
    request_id: str
    sku: str
    quantity: int
    original_ttl: int | float | None = None
    expires_at: int | float | None = None
    status: str = "reserved"

    def snapshot(self) -> dict[str, str | int | float | None]:
        return {
            "request_id": self.request_id,
            "sku": self.sku,
            "quantity": self.quantity,
            "status": self.status,
            "expires_at": self.expires_at,
        }


class Inventory:
    """Own stock balances and the lifetime of each successful request ID.

    Free stock is updated only by stocking, a new reservation, or the first
    cancellation or expiration. Terminal records remain to enforce idempotency.
    """

    def __init__(self, clock: Callable[[], int | float] | None = None) -> None:
        self._clock = time.monotonic if clock is None else clock
        self._available: dict[str, int] = {}
        self._reservations: dict[str, _Reservation] = {}

    def _expire(self, now: int | float) -> None:
        """Release elapsed reservations once, using one time per operation."""
        for request_id, reservation in self._reservations.items():
            if (
                reservation.status == "reserved"
                and reservation.expires_at is not None
                and now >= reservation.expires_at
            ):
                self._reservations[request_id] = replace(reservation, status="expired")
                self._available[reservation.sku] += reservation.quantity

    def stock(self, sku: str, quantity: int) -> None:
        """Add a positive quantity of stock for a valid SKU."""
        _validate_identifier(sku, "sku")
        _validate_quantity(quantity)
        self._available[sku] = self._available.get(sku, 0) + quantity

    def available(self, sku: str) -> int:
        """Return unreserved stock, or zero for an unknown valid SKU."""
        _validate_identifier(sku, "sku")
        self._expire(self._clock())
        return self._available.get(sku, 0)

    def reserve(
        self, request_id: str, sku: str, quantity: int,
        ttl_seconds: int | float | None = None,
    ) -> dict[str, str | int | float | None]:
        """Reserve stock once, or return the current state of an exact replay."""
        _validate_identifier(request_id, "request_id")
        _validate_identifier(sku, "sku")
        _validate_quantity(quantity)
        if ttl_seconds is not None:
            _validate_ttl(ttl_seconds)

        now = self._clock()
        self._expire(now)

        existing = self._reservations.get(request_id)
        if existing is not None:
            if (
                existing.sku != sku
                or existing.quantity != quantity
                or existing.original_ttl != ttl_seconds
            ):
                raise Conflict("request_id already has different reservation details")
            return existing.snapshot()

        available = self._available.get(sku, 0)
        if quantity > available:
            raise OutOfStock("quantity exceeds available stock")

        expires_at = None if ttl_seconds is None else now + ttl_seconds
        reservation = _Reservation(request_id, sku, quantity, ttl_seconds, expires_at)
        self._available[sku] = available - quantity
        self._reservations[request_id] = reservation
        return reservation.snapshot()

    def cancel(self, request_id: str) -> bool:
        """Cancel an active reservation, releasing its stock exactly once."""
        _validate_identifier(request_id, "request_id")
        self._expire(self._clock())
        reservation = self._reservations.get(request_id)
        if reservation is None or reservation.status != "reserved":
            return False

        self._reservations[request_id] = replace(reservation, status="cancelled")
        self._available[reservation.sku] += reservation.quantity
        return True

    def get_reservation(
        self, request_id: str
    ) -> dict[str, str | int | float | None] | None:
        """Return an independent snapshot, or None for an unknown valid ID."""
        _validate_identifier(request_id, "request_id")
        self._expire(self._clock())
        reservation = self._reservations.get(request_id)
        return None if reservation is None else reservation.snapshot()

    def renew(
        self, request_id: str, ttl_seconds: int | float
    ) -> dict[str, str | int | float | None]:
        """Set an active reservation's expiry without changing its request signature."""
        _validate_identifier(request_id, "request_id")
        _validate_ttl(ttl_seconds)
        now = self._clock()
        self._expire(now)
        reservation = self._reservations.get(request_id)
        if reservation is None or reservation.status != "reserved":
            raise ValueError("only an active reservation can be renewed")

        renewed = replace(reservation, expires_at=now + ttl_seconds)
        self._reservations[request_id] = renewed
        return renewed.snapshot()
