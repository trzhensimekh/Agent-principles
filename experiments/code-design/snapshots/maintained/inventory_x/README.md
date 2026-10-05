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
returns its current snapshot, including after cancellation or expiration.
Reusing an ID with different original SKU, quantity, or TTL raises `Conflict`;
numerically equal TTLs such as `5` and `5.0` count as equal. Insufficient stock
raises `OutOfStock` without consuming the ID. Both exceptions inherit from
`ValueError`. Every returned reservation dictionary is an independent copy
with `request_id`, `sku`, `quantity`, `status`, and `expires_at` fields.

Pass `ttl_seconds` to `reserve` to create a timed reservation. It must be a
positive finite `int` or `float`, excluding booleans. The default `None` means
no expiry and produces `expires_at=None`. Invalid TTLs raise `ValueError`
before changing reservations or consuming request IDs.

`Inventory(clock=None)` uses `time.monotonic` by default. An injected clock
must take no arguments and return nonnegative finite seconds that never
decrease. Deadlines use the clock's time scale, rather than wall-clock dates.

```python
now = 100.0
inventory = Inventory(clock=lambda: now)
inventory.stock("widget", 5)
reservation = inventory.reserve("timed-order", "widget", 2, ttl_seconds=10)
assert reservation["expires_at"] == 110.0

now = 105.0
renewed = inventory.renew("timed-order", ttl_seconds=20)
assert renewed["expires_at"] == 125.0
# Replay still uses the original TTL and returns the renewed deadline.
assert inventory.reserve("timed-order", "widget", 2, 10) == renewed

now = 125.0
assert inventory.cancel("timed-order") is False
assert inventory.get_reservation("timed-order")["status"] == "expired"
assert inventory.available("widget") == 5
```

A reservation is active only while `now < expires_at`. At the deadline it
becomes terminally `expired` and releases its units once. Expiration is
observed lazily by `available`, `reserve`, `cancel`, `get_reservation`, and
`renew`; there is no background thread. Replay never restarts the timer.
Cancelling before the deadline instead leaves a terminal `cancelled` record.

`renew(request_id, ttl_seconds)` sets an active reservation's deadline to
the current time plus the supplied positive finite TTL. It can extend or
shorten an existing deadline, or add one to a non-expiring reservation.
Renewal preserves the original request signature and returns a defensive
snapshot. `None` is invalid for renewal. Unknown, cancelled, and expired
IDs raise `ValueError`; renewal never revives a terminal reservation.

Internally, dictionaries track available units and reservation records.
Cancelled and expired records remain stored to preserve request identity
and replay behavior. Expiration checks scan the retained records. There is
no persistence, I/O, or concurrency support.

Run the tests from this directory:

```sh
python -m unittest -v
```
