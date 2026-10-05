"""In-memory stock reservations for single-threaded use."""

from dataclasses import dataclass, replace

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


@dataclass(frozen=True, slots=True)
class _Reservation:
    request_id: str
    sku: str
    quantity: int
    status: str = "reserved"

    def snapshot(self) -> dict[str, str | int]:
        return {
            "request_id": self.request_id,
            "sku": self.sku,
            "quantity": self.quantity,
            "status": self.status,
        }


class Inventory:
    """Own stock balances and the lifetime of each successful request ID.

    Free stock is updated only by stocking, a new reservation, or the first
    cancellation. Records remain after cancellation to enforce idempotency.
    """

    def __init__(self) -> None:
        self._available: dict[str, int] = {}
        self._reservations: dict[str, _Reservation] = {}

    def stock(self, sku: str, quantity: int) -> None:
        """Add a positive quantity of stock for a valid SKU."""
        _validate_identifier(sku, "sku")
        _validate_quantity(quantity)
        self._available[sku] = self._available.get(sku, 0) + quantity

    def available(self, sku: str) -> int:
        """Return unreserved stock, or zero for an unknown valid SKU."""
        _validate_identifier(sku, "sku")
        return self._available.get(sku, 0)

    def reserve(
        self, request_id: str, sku: str, quantity: int
    ) -> dict[str, str | int]:
        """Reserve stock once, or return the current state of an exact replay."""
        _validate_identifier(request_id, "request_id")
        _validate_identifier(sku, "sku")
        _validate_quantity(quantity)

        existing = self._reservations.get(request_id)
        if existing is not None:
            if existing.sku != sku or existing.quantity != quantity:
                raise Conflict("request_id already has different reservation details")
            return existing.snapshot()

        available = self._available.get(sku, 0)
        if quantity > available:
            raise OutOfStock("quantity exceeds available stock")

        reservation = _Reservation(request_id, sku, quantity)
        self._available[sku] = available - quantity
        self._reservations[request_id] = reservation
        return reservation.snapshot()

    def cancel(self, request_id: str) -> bool:
        """Cancel an active reservation, releasing its stock exactly once."""
        _validate_identifier(request_id, "request_id")
        reservation = self._reservations.get(request_id)
        if reservation is None or reservation.status == "cancelled":
            return False

        self._reservations[request_id] = replace(reservation, status="cancelled")
        self._available[reservation.sku] += reservation.quantity
        return True

    def get_reservation(self, request_id: str) -> dict[str, str | int] | None:
        """Return an independent snapshot, or None for an unknown valid ID."""
        _validate_identifier(request_id, "request_id")
        reservation = self._reservations.get(request_id)
        return None if reservation is None else reservation.snapshot()
