# Integer-cent pricing

Python 3.11+; standard library only.

```python
from pricing import quote

result = quote(
    [{"sku": "A", "unit_price_cents": 101, "quantity": 3}],
    discount_percent=17,
    shipping_cents=99,
    tax_percent=7,
)
# {'subtotal_cents': 303, 'discount_cents': 51, 'shipping_cents': 99,
#  'tax_cents': 17, 'total_cents': 368,
#  'lines': [{'sku': 'A', 'subtotal_cents': 303, 'discount_cents': 51,
#             'net_cents': 252, 'taxable': True}]}
```

The complete signature is:

```python
quote(items, discount_percent=0, shipping_cents=0, tax_percent=0,
      discount_cap_cents=None, shipping_taxable=False)
```

`items` must be a nonempty list of dictionaries, each with a nonempty string
`sku`, nonnegative integer `unit_price_cents`, and positive integer `quantity`.
Optional item flags `discountable` and `taxable` both default to `True` and must
be booleans; integer `0` and `1` are rejected. Repeated SKUs and zero prices are
allowed. Percentages default to zero and must be integers from 0 through 100.
Shipping defaults to zero and must be a nonnegative integer. The discount cap
is `None` (no cap) or a nonnegative integer. `shipping_taxable` must be a boolean
and defaults to `False`. Booleans are rejected for all numeric inputs. Invalid
inputs raise `ValueError`; inputs are never mutated.

Each row subtotal is price times quantity. The discount is rounded down on the
sum of discountable row subtotals, then limited by the optional cap. It is
allocated proportionally across those rows: each row receives its integer
share, then leftover cents go to the largest fractional remainders, with ties
resolved in input order. Zero eligible subtotal produces zero discount.

Tax is rounded down once on the sum of taxable rows' net amounts, plus shipping
when `shipping_taxable=True`. Tax is never rounded per row. Total is subtotal
minus discount plus shipping and tax. Defaults preserve the original monetary
results: all rows are discountable and taxable, and shipping is excluded from tax.

The result contains the five totals shown above plus `lines`, a fresh list of
dictionaries in input order. Each line contains `sku`, `subtotal_cents`,
`discount_cents`, `net_cents`, and `taxable`; repeated SKUs remain separate rows.
For example, two one-cent rows with a 50% discount produce one cent of total
discount, assigned to the first row. A non-taxable first row therefore leaves
the second row's full cent in the tax base.

All arithmetic uses integers, including for arbitrarily large amounts. Calls
are independent and deterministic, with no persistent state or I/O.

Run the tests from this directory:

```sh
python3 -m unittest -v
```
