# Build an in-memory inventory reservation library

Implement a Python 3.11+ standard-library module `inventory.py`. Expose `Inventory`, `OutOfStock(ValueError)`, and `Conflict(ValueError)`. This is a single-process, single-threaded library; persistence, I/O and concurrency are out of scope. Choose the internal architecture yourself. Write focused tests and a short README. Do not install dependencies.

API and behavior:

- `Inventory()` starts empty.
- `stock(sku, quantity)` adds stock. SKU is a nonempty string; quantity is a positive integer, not bool. Invalid input raises ValueError without changing state.
- `available(sku)` returns stocked quantity minus active reservations; unknown valid SKU returns zero. SKU validation is the same.
- `reserve(request_id, sku, quantity)` reserves stock and returns a dict with `request_id`, `sku`, `quantity`, `status`. Status is `reserved` or `cancelled`. IDs are nonempty strings. Quantity is a positive integer, not bool. Invalid input raises ValueError without changing state.
- A reservation exceeding available stock raises OutOfStock without changing any state or consuming the request ID. A later valid retry may succeed.
- Repeating a successful request ID with the same SKU and quantity returns its current snapshot and does not reserve stock twice. The same ID with different SKU or quantity raises Conflict, including after cancellation. A cancelled reservation cannot be resurrected by replay.
- `cancel(request_id)` returns True only when it changes an active reservation to cancelled and releases its stock. Unknown or already cancelled IDs return False. Invalid ID raises ValueError.
- `get_reservation(request_id)` returns its current snapshot or None for an unknown valid ID. Invalid ID raises ValueError.
- Returned dictionaries must be defensive copies: callers cannot mutate internal state through them.

Keep behavior consistent across all public entry points. No additional public interface is required.
