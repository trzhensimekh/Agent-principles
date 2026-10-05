# Add expiring reservations to the inventory library

Extend the existing library, preserving initial behavior when no expiry is requested. Do not redesign the public interface beyond the additions below. Read the existing source and tests yourself; no previous agent conversation is available. Add focused regression tests and update the README.

- `Inventory(clock=None)` optionally takes a zero-argument clock returning a nonnegative finite number of seconds. Without it, use time.monotonic. The clock can be assumed nondecreasing; thread safety and persistence remain out of scope.
- `reserve(request_id, sku, quantity, ttl_seconds=None)` accepts None (no expiration) or a positive finite int/float, excluding bool. Invalid TTL raises ValueError without consuming the ID or changing a live reservation.
- A new timed reservation records `expires_at = clock() + ttl_seconds`. The returned snapshot gains `expires_at`, with None for no expiry.
- A timed reservation is active exactly while now < expires_at. At now == expires_at it transitions to terminal status `expired` and releases stock. `available`, `reserve`, `cancel`, `get_reservation`, and `renew` must observe expired reservations consistently. Lazy expiration on those methods is sufficient; no background thread.
- Replaying a request ID compares the original request's SKU, quantity, and TTL. Identical parameters return the current snapshot, including after expiry; they never restart the timer or reserve again. Different original parameters raise Conflict. Numerically equal TTLs such as 5 and 5.0 count as equal.
- `renew(request_id, ttl_seconds)` requires a positive finite TTL (None invalid). It returns a current snapshot after setting an active reservation's expiry to now + TTL; this also works for a previously non-expiring active reservation. Unknown, cancelled, or expired IDs raise ValueError. A failed renewal must not reserve stock or revive a terminal reservation. Renewing does not change the original request signature used for replay/conflict checks.
- Cancellation at or after expiry returns False; the reservation remains expired.
- Returned snapshots remain defensive copies. Validation of SKU/IDs/quantity and original exception types remains unchanged. Do not accept NaN, infinity, bool TTLs, or negative values.
