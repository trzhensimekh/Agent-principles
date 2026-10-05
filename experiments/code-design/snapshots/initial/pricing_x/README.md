# Integer-cent quotes

`pricing.py` provides `quote(items, discount_percent=0, shipping_cents=0,
tax_percent=0)` for Python 3.11 or newer. It uses only the standard library.

```python
from pricing import quote

result = quote(
    [{"sku": "widget", "unit_price_cents": 101, "quantity": 1}],
    discount_percent=50,
    shipping_cents=99,
    tax_percent=50,
)
# {'subtotal_cents': 101, 'discount_cents': 50, 'shipping_cents': 99,
#  'tax_cents': 25, 'total_cents': 175}
```

Items must be a nonempty list of dictionaries with a nonempty string `sku`,
nonnegative integer `unit_price_cents`, and positive integer `quantity`.
Repeated SKUs and zero prices are accepted. Extra dictionary fields are ignored.
Percentages are integers from 0 through 100; shipping is a nonnegative integer.
Booleans are rejected for all integer inputs. Invalid inputs raise `ValueError`.

The discount rounds down once on the complete subtotal. Tax rounds down on the
discounted subtotal; shipping is not taxable. Integer arithmetic preserves exact
amounts even for very large values. Calls do not mutate inputs and return a fresh
dictionary each time. The library performs no I/O.

Run the tests from this directory:

```sh
python -m unittest -v
```
