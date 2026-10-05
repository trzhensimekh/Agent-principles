"""Compute exact integer-cent quotes without modifying caller inputs."""


def _require_integer(value, name, minimum, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer excluding bool")
    if value < minimum or (maximum is not None and value > maximum):
        bounds = f"at least {minimum}" if maximum is None else f"from {minimum} to {maximum}"
        raise ValueError(f"{name} must be {bounds}")


def _require_boolean(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")


def quote(items, discount_percent=0, shipping_cents=0, tax_percent=0,
          discount_cap_cents=None, shipping_taxable=False):
    """Return integer-cent totals and one breakdown per input row.

    Items must be a nonempty list of dictionaries with a nonempty string
    ``sku``, nonnegative integer ``unit_price_cents``, and positive integer
    ``quantity``. Percentages must be integers in [0, 100], and shipping
    must be a nonnegative integer. Booleans are not accepted as integers.
    Optional item flags ``discountable`` and ``taxable`` default to True
    and must be booleans, as must ``shipping_taxable``. A discount cap is
    None or a nonnegative integer excluding bool. Invalid input raises
    ValueError. Caller inputs are never modified.

    Discount is rounded down on eligible rows, capped, then allocated by
    largest remainders with input order breaking ties. Tax is rounded down
    once on taxable rows' net amounts, including shipping only when requested.
    """
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a nonempty list of dictionaries")

    _require_integer(discount_percent, "discount_percent", 0, 100)
    _require_integer(shipping_cents, "shipping_cents", 0)
    _require_integer(tax_percent, "tax_percent", 0, 100)
    if discount_cap_cents is not None:
        _require_integer(discount_cap_cents, "discount_cap_cents", 0)
    _require_boolean(shipping_taxable, "shipping_taxable")

    subtotal = 0
    eligible_subtotal = 0
    eligible_indices = []
    lines = []
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
        discountable = item.get("discountable", True)
        taxable = item.get("taxable", True)
        _require_boolean(discountable, f"items[{index}].discountable")
        _require_boolean(taxable, f"items[{index}].taxable")
        row_subtotal = item["unit_price_cents"] * item["quantity"]
        subtotal += row_subtotal
        if discountable:
            eligible_subtotal += row_subtotal
            eligible_indices.append(index)
        lines.append({
            "sku": item["sku"],
            "subtotal_cents": row_subtotal,
            "discount_cents": 0,
            "net_cents": row_subtotal,
            "taxable": taxable,
        })

    discount = eligible_subtotal * discount_percent // 100
    if discount_cap_cents is not None:
        discount = min(discount, discount_cap_cents)

    if discount:
        # A positive discount implies a positive eligible subtotal.
        remainders = []
        allocated = 0
        for index in eligible_indices:
            line = lines[index]
            share, remainder = divmod(
                discount * line["subtotal_cents"], eligible_subtotal
            )
            line["discount_cents"] = share
            allocated += share
            remainders.append((remainder, index))
        remainders.sort(key=lambda entry: (-entry[0], entry[1]))
        for _, index in remainders[:discount - allocated]:
            lines[index]["discount_cents"] += 1

    tax_base = shipping_cents if shipping_taxable else 0
    for line in lines:
        line["net_cents"] -= line["discount_cents"]
        if line["taxable"]:
            tax_base += line["net_cents"]
    tax = tax_base * tax_percent // 100
    return {
        "subtotal_cents": subtotal,
        "discount_cents": discount,
        "shipping_cents": shipping_cents,
        "tax_cents": tax,
        "total_cents": subtotal - discount + shipping_cents + tax,
        "lines": lines,
    }
