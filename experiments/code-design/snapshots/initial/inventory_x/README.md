# In-memory inventory

`inventory.py` is a Python 3.11+ standard-library library for a single process
and thread. Import `Inventory`, `OutOfStock`, and `Conflict` directly.

```python
from inventory import Inventory

inventory = Inventory()
inventory.stock("widget", 5)
reservation = inventory.reserve("order-42", "widget", 2)
assert inventory.available("widget") == 3
assert inventory.reserve("order-42", "widget", 2) == reservation
assert inventory.cancel("order-42") is True
assert inventory.get_reservation("order-42")["status"] == "cancelled"
assert inventory.available("widget") == 5
```

SKUs and request IDs must be nonempty strings; quantities must be positive
integers excluding booleans. Invalid inputs raise `ValueError` before mutation.
Unknown SKUs have zero available units. Unknown reservation IDs return `None`
from `get_reservation` and `False` from `cancel`.

Reservations consume available units once. Replaying the same ID and details
returns its current snapshot, including after cancellation. Reusing an ID with
different details raises `Conflict`; insufficient stock raises `OutOfStock`
without consuming the ID. Both exceptions inherit from `ValueError`. Every
returned reservation dictionary is an independent copy.

Internally, dictionaries track available units and reservation records.
Cancelled records remain stored to preserve request identity and replay
behavior. There is no persistence, I/O, concurrency support, or automatic
record expiration.

Run the tests from this directory:

```sh
python -m unittest -v
```
