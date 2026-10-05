"""Compute exact integer-cent quotes without modifying caller inputs."""


def _require_integer(value, name, minimum, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer excluding bool")
    if value < minimum or (maximum is not None and value > maximum):
        bounds = f"at least {minimum}" if maximum is None else f"from {minimum} to {maximum}"
        raise ValueError(f"{name} must be {bounds}")


def quote(items, discount_percent=0, shipping_cents=0, tax_percent=0):
    """Return subtotal, discount, shipping, tax, and total in integer cents.

    Items must be a nonempty list of dictionaries with a nonempty string
    ``sku``, nonnegative integer ``unit_price_cents``, and positive integer
    ``quantity``. Percentages must be integers in [0, 100], and shipping
    must be a nonnegative integer. Booleans are not accepted as integers.
    Invalid input raises ValueError.

    Discount and tax are rounded down independently. Tax applies to the
    discounted subtotal and excludes shipping.
    """
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a nonempty list of dictionaries")

    _require_integer(discount_percent, "discount_percent", 0, 100)
    _require_integer(shipping_cents, "shipping_cents", 0)
    _require_integer(tax_percent, "tax_percent", 0, 100)

    subtotal = 0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be a dictionary")
        for key in ("sku", "unit_price_cents", "quantity"):
            if key not in item:
                raise ValueError(f"items[{index}] is missing {key}")
        if not isinstance(item["sku"], str) or not item["sku"]:
            raise ValueError(f"items[{index}].sku must be a nonempty string")
        _require_integer(item["unit_price_cents"], f"items[{index}].unit_price_cents", 0)
        _require_integer(item["quantity"], f"items[{index}].quantity", 1)
        subtotal += item["unit_price_cents"] * item["quantity"]

    discount = subtotal * discount_percent // 100
    tax = (subtotal - discount) * tax_percent // 100
    return {
        "subtotal_cents": subtotal,
        "discount_cents": discount,
        "shipping_cents": shipping_cents,
        "tax_cents": tax,
        "total_cents": subtotal - discount + shipping_cents + tax,
    }
