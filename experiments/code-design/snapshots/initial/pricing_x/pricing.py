"""Deterministic quotes using exact integer-cent arithmetic."""

__all__ = ["quote"]


def _validate_integer(
    value: object,
    name: str,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    """Validate integer bounds while excluding booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer excluding bool")
    if value < minimum or (maximum is not None and value > maximum):
        bounds = f"at least {minimum}" if maximum is None else f"from {minimum} to {maximum}"
        raise ValueError(f"{name} must be {bounds}")
    return value


def _subtotal_cents(items: object) -> int:
    """Validate every line item and sum its extended price in cents."""
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a nonempty list of dictionaries")

    subtotal = 0
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be a dictionary")
        sku = item.get("sku")
        if not isinstance(sku, str) or not sku:
            raise ValueError(f"{prefix}.sku must be a nonempty string")
        unit_price = _validate_integer(
            item.get("unit_price_cents"), f"{prefix}.unit_price_cents"
        )
        quantity = _validate_integer(
            item.get("quantity"), f"{prefix}.quantity", minimum=1
        )
        subtotal += unit_price * quantity
    return subtotal


def quote(
    items: list[dict[str, object]],
    discount_percent: int = 0,
    shipping_cents: int = 0,
    tax_percent: int = 0,
) -> dict[str, int]:
    """Return an itemized quote in cents without changing caller inputs.

    Discount and tax percentages must be integers in [0, 100]. Discount
    applies to the subtotal; tax applies after discount, excluding shipping.
    Both amounts round down to whole cents. Invalid inputs raise ValueError.
    """
    discount_percent = _validate_integer(
        discount_percent, "discount_percent", maximum=100
    )
    shipping_cents = _validate_integer(shipping_cents, "shipping_cents")
    tax_percent = _validate_integer(tax_percent, "tax_percent", maximum=100)
    subtotal = _subtotal_cents(items)

    discount = subtotal * discount_percent // 100
    discounted_subtotal = subtotal - discount
    tax = discounted_subtotal * tax_percent // 100
    return {
        "subtotal_cents": subtotal,
        "discount_cents": discount,
        "shipping_cents": shipping_cents,
        "tax_cents": tax,
        "total_cents": discounted_subtotal + shipping_cents + tax,
    }
