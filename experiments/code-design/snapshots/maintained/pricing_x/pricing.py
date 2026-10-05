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


def _validate_boolean(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _validated_rows(items: object) -> list[tuple[str, int, bool, bool]]:
    """Return fresh (sku, subtotal, discountable, taxable) rows."""
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a nonempty list of dictionaries")

    rows = []
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
        discountable = _validate_boolean(
            item.get("discountable", True), f"{prefix}.discountable"
        )
        taxable = _validate_boolean(item.get("taxable", True), f"{prefix}.taxable")
        rows.append((sku, unit_price * quantity, discountable, taxable))
    return rows


def _allocate_discount(weights: list[int], discount: int) -> list[int]:
    """Allocate cents by largest remainder, breaking ties by input order."""
    allocations = [0] * len(weights)
    if discount == 0:
        return allocations

    eligible_subtotal = sum(weights)
    remainders = []
    for index, weight in enumerate(weights):
        if weight:
            allocations[index], remainder = divmod(discount * weight, eligible_subtotal)
            remainders.append((-remainder, index))

    remaining = discount - sum(allocations)
    for _, index in sorted(remainders)[:remaining]:
        allocations[index] += 1
    return allocations


def quote(
    items: list[dict[str, object]],
    discount_percent: int = 0,
    shipping_cents: int = 0,
    tax_percent: int = 0,
    discount_cap_cents: int | None = None,
    shipping_taxable: bool = False,
) -> dict[str, object]:
    """Return an itemized quote in cents without changing caller inputs.

    Discount applies to discountable rows, subject to an optional cent cap.
    Its cents are allocated proportionally using largest remainders, with
    input order breaking ties. Tax rounds down once on taxable row nets plus
    shipping when shipping_taxable is True. Invalid inputs raise ValueError.
    """
    discount_percent = _validate_integer(
        discount_percent, "discount_percent", maximum=100
    )
    shipping_cents = _validate_integer(shipping_cents, "shipping_cents")
    tax_percent = _validate_integer(tax_percent, "tax_percent", maximum=100)
    if discount_cap_cents is not None:
        discount_cap_cents = _validate_integer(discount_cap_cents, "discount_cap_cents")
    shipping_taxable = _validate_boolean(shipping_taxable, "shipping_taxable")
    rows = _validated_rows(items)

    subtotal = sum(row_subtotal for _, row_subtotal, _, _ in rows)
    weights = [row_subtotal if discountable else 0
               for _, row_subtotal, discountable, _ in rows]
    discount = sum(weights) * discount_percent // 100
    if discount_cap_cents is not None:
        discount = min(discount, discount_cap_cents)
    allocations = _allocate_discount(weights, discount)

    lines = []
    tax_base = shipping_cents if shipping_taxable else 0
    for (sku, row_subtotal, _, taxable), allocated in zip(rows, allocations):
        net = row_subtotal - allocated
        lines.append({
            "sku": sku,
            "subtotal_cents": row_subtotal,
            "discount_cents": allocated,
            "net_cents": net,
            "taxable": taxable,
        })
        if taxable:
            tax_base += net

    discounted_subtotal = subtotal - discount
    tax = tax_base * tax_percent // 100
    return {
        "subtotal_cents": subtotal,
        "discount_cents": discount,
        "shipping_cents": shipping_cents,
        "tax_cents": tax,
        "total_cents": discounted_subtotal + shipping_cents + tax,
        "lines": lines,
    }
