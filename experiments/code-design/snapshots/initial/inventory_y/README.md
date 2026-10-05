# Inventory reservations

`inventory.py` is a Python 3.11+ in-memory reservation library using only the
standard library. Each `Inventory` owns its free stock balances and private,
immutable reservation records. Returned dictionaries are independent snapshots.

```python
from inventory import Inventory

inventory = Inventory()
inventory.stock("widget", 5)
reservation = inventory.reserve("order-1", "widget", 2)
assert inventory.available("widget") == 3
assert inventory.cancel("order-1") is True
assert inventory.available("widget") == 5
assert inventory.get_reservation("order-1")["status"] == "cancelled"
```

SKUs and request IDs must be nonempty strings; quantities must be positive
integers (booleans are rejected). Invalid input raises `ValueError` without
changing state. Unknown SKUs have zero available stock. Unknown reservation IDs
return `None` from `get_reservation` and `False` from `cancel`.

`OutOfStock`, a `ValueError` subclass, leaves the request ID free for a later
retry. Reusing a successful request ID with the same SKU and quantity returns
its current status without reserving again, even after cancellation. Different
details raise `Conflict`, also a `ValueError` subclass. Cancellation releases
stock only once. Successful request IDs remain stored for the inventory's
lifetime to preserve these rules.

This library supports one process and one thread. It provides no persistence,
I/O, or concurrency coordination.

Run the tests from this directory:

```sh
python -m unittest -v
```
