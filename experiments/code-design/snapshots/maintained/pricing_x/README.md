# Integer-cent quotes

`pricing.py` provides `quote(items, discount_percent=0, shipping_cents=0,
tax_percent=0, discount_cap_cents=None, shipping_taxable=False)` for Python 3.11
or newer. It uses only the standard library.

```python
from pricing import quote

result = quote(
    [{"sku": "widget", "unit_price_cents": 101, "quantity": 1}],
    discount_percent=50,
    shipping_cents=99,
    tax_percent=50,
)
# {'subtotal_cents': 101, 'discount_cents': 50, 'shipping_cents': 99,
#  'tax_cents': 25, 'total_cents': 175,
#  'lines': [{'sku': 'widget', 'subtotal_cents': 101, 'discount_cents': 50,
#             'net_cents': 51, 'taxable': True}]}
```

Items must be a nonempty list of dictionaries with a nonempty string `sku`,
nonnegative integer `unit_price_cents`, and positive integer `quantity`.
Each item may also have boolean `discountable` and `taxable` fields; both default
to `True`. Repeated SKUs remain separate rows, and zero prices are accepted.
Other dictionary fields are ignored.
Percentages are integers from 0 through 100; shipping is a nonnegative integer.
`discount_cap_cents` is `None` or a nonnegative integer. Booleans are rejected for
all integer inputs. `shipping_taxable` must be a boolean, as must the item flags;
integers `0` and `1` are not accepted as flags. Invalid inputs raise `ValueError`.

The discount is the eligible subtotal times `discount_percent`, rounded down to
cents and limited by `discount_cap_cents` when supplied. Only discountable rows
contribute to the eligible subtotal. If that subtotal is zero, the discount is
zero. The discount is allocated proportionally across eligible rows: start with
each row's share rounded down, then give remaining cents to the largest fractional
remainders, breaking ties in original input order. Non-discountable and zero-price
rows receive no discount.

Tax is calculated once on the sum of taxable row nets, adding shipping only when
`shipping_taxable=True`, then rounded down to cents. For example, two one-cent
taxable rows at 50% tax produce one cent of tax. Tax is never rounded per row.
Total is subtotal minus discount plus shipping plus tax. Omitting the new arguments
and item flags preserves the original monetary outputs.

The result includes the five aggregate amounts shown above and `lines` in input
order. Each line contains `sku`, `subtotal_cents`, `discount_cents`, `net_cents`,
and `taxable`. Integer arithmetic preserves exact amounts even for very large
values. Calls do not mutate inputs and return fresh dictionaries and line lists
each time. The library performs no I/O.

Run the tests from this directory:

```sh
python -m unittest -v
```
