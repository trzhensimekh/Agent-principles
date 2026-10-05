# Inventory reservations

`inventory.py` is a Python 3.11+ in-memory reservation library using only the
standard library. Each `Inventory` owns its free stock balances and private,
immutable reservation records. Returned dictionaries are independent snapshots.
They contain `request_id`, `sku`, `quantity`, `status`, and `expires_at`.

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
its current snapshot without reserving again. The original TTL is also part of
that comparison: `5` and `5.0` are equal, but `None` and `5` differ. Different
details raise `Conflict`, also a `ValueError` subclass, including after
cancellation or expiration. Successful request IDs remain stored for the
inventory's lifetime to preserve these rules.

Pass `ttl_seconds` to `reserve` to expire a reservation. Omit it or pass `None`
for no expiration (`expires_at` is then `None`). A TTL must be a positive finite
`int` or `float`; booleans, NaN, infinity, and other types raise `ValueError`.
`Inventory(clock=None)` uses `time.monotonic` by default. An injected clock must
be a zero-argument callable returning nonnegative finite seconds in nondecreasing
order. Deadlines use that clock's time scale, rather than calendar timestamps.

```python
now = [100.0]
inventory = Inventory(clock=lambda: now[0])
inventory.stock("widget", 5)
assert inventory.reserve("timed", "widget", 2, ttl_seconds=5)["expires_at"] == 105
now[0] = 103
assert inventory.renew("timed", 10)["expires_at"] == 113
# Replay still uses the original TTL and returns the renewed deadline.
assert inventory.reserve("timed", "widget", 2, 5.0)["expires_at"] == 113
now[0] = 113
assert inventory.get_reservation("timed")["status"] == "expired"
assert inventory.available("widget") == 5
assert inventory.cancel("timed") is False
```

Expiration happens exactly when `now >= expires_at` and releases stock once.
`available`, `reserve`, `cancel`, `get_reservation`, and `renew` check for elapsed
deadlines lazily; there is no background worker. Expiration checks scan the stored
reservations. Both `cancelled` and `expired` are terminal states: replay never
restarts a timer, and cancellation at or after expiry returns `False`.

`renew(request_id, ttl_seconds)` sets an active reservation's deadline to
`clock() + ttl_seconds`, including for a previously non-expiring reservation.
It can shorten or extend the deadline and returns a new snapshot. The original
request signature is unchanged. Unknown, cancelled, or expired IDs raise
`ValueError`; `None` is invalid for renewal. Invalid TTLs leave live reservations
unchanged and do not consume request IDs.

This library supports one process and one thread. It provides no persistence,
I/O, or concurrency coordination.

Run the tests from this directory:

```sh
python -m unittest -v
```
