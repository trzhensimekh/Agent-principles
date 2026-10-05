"""Ledger contract: immutable orders, unique requests, and an atomic outbox."""

from typing import Protocol

from .domain import Order, RefundRequest


class RefundLedger(Protocol):
    def get_order(self, order_id: str) -> Order:
        """Return an immutable order snapshot, or raise KeyError."""
        ...

    def get_request(self, request_id: str) -> RefundRequest | None:
        """Return the original request for an idempotency key, if present."""
        ...

    def record(self, request: RefundRequest) -> RefundRequest:
        """Atomically save a request and one refund.requested outbox event.

        Same key + same order returns the original request, including its time.
        Same key + different order raises RequestConflict. A second key for the
        same order raises AlreadyRequested. On failure, neither write survives.
        Order identity, amount and state are immutable after insertion.
        """
        ...
