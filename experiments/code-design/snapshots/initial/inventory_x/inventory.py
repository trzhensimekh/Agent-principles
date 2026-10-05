"""Single-process, in-memory stock reservations with idempotent request IDs."""

from dataclasses import dataclass

__all__ = ["Inventory", "OutOfStock", "Conflict"]


class OutOfStock(ValueError):
    """The requested quantity exceeds the currently available stock."""


class Conflict(ValueError):
    """A request ID was previously used with different reservation details."""


def _validate_string(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")


def _validate_quantity(quantity: int) -> None:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("quantity must be a positive integer, not bool")


@dataclass
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
    """Track available units and retain reservations, including cancellations."""

    def __init__(self) -> None:
        self._available: dict[str, int] = {}
        self._reservations: dict[str, _Reservation] = {}

    def stock(self, sku: str, quantity: int) -> None:
        """Add units to a SKU's available stock."""
        _validate_string(sku, "sku")
        _validate_quantity(quantity)
        self._available[sku] = self._available.get(sku, 0) + quantity

    def available(self, sku: str) -> int:
        """Return the unreserved units of a SKU, or zero for an unknown SKU."""
        _validate_string(sku, "sku")
        return self._available.get(sku, 0)

    def reserve(self, request_id: str, sku: str, quantity: int) -> dict[str, str | int]:
        """Reserve units once per request ID, or return its current snapshot."""
        _validate_string(request_id, "request_id")
        _validate_string(sku, "sku")
        _validate_quantity(quantity)

        existing = self._reservations.get(request_id)
        if existing is not None:
            if existing.sku != sku or existing.quantity != quantity:
                raise Conflict("request ID already has different reservation details")
            return existing.snapshot()

        available = self._available.get(sku, 0)
        if quantity > available:
            raise OutOfStock(f"insufficient stock for {sku!r}")

        reservation = _Reservation(request_id, sku, quantity)
        self._available[sku] = available - quantity
        self._reservations[request_id] = reservation
        return reservation.snapshot()

    def cancel(self, request_id: str) -> bool:
        """Cancel an active reservation and release its units exactly once."""
        _validate_string(request_id, "request_id")
        reservation = self._reservations.get(request_id)
        if reservation is None or reservation.status == "cancelled":
            return False
        self._available[reservation.sku] += reservation.quantity
        reservation.status = "cancelled"
        return True

    def get_reservation(self, request_id: str) -> dict[str, str | int] | None:
        """Return an independent snapshot, or None for an unknown request ID."""
        _validate_string(request_id, "request_id")
        reservation = self._reservations.get(request_id)
        return None if reservation is None else reservation.snapshot()
