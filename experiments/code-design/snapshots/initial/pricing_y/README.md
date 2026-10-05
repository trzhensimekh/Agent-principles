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
#  'tax_cents': 17, 'total_cents': 368}
```

`items` must be a nonempty list of dictionaries, each with a nonempty string
`sku`, nonnegative integer `unit_price_cents`, and positive integer `quantity`.
Repeated SKUs and zero prices are allowed. Percentages default to zero and must
be integers from 0 through 100. Shipping defaults to zero and must be a
nonnegative integer. Booleans are rejected for numeric inputs. Invalid inputs
raise `ValueError`; inputs are never mutated.

The subtotal sums price times quantity. Discount is rounded down on the subtotal;
tax is rounded down on the discounted subtotal. Shipping is excluded from tax.
Total is subtotal minus discount plus shipping and tax. All arithmetic uses
integers, including for arbitrarily large amounts. Each call returns a fresh
dictionary and has no persistent state or I/O.

Run the tests from this directory:

```sh
python3 -m unittest -v
```
