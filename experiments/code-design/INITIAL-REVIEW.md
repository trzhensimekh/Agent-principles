# Condition-blind qualitative review of initial implementations

## Scope and method

Reviewed only `tasks/inventory-initial.md`, `tasks/pricing-initial.md`, and the Python files and READMEs under `snapshots/initial/{inventory_x,inventory_y,pricing_x,pricing_y}`. Did not read condition guidance, registration, active implementations, maintenance tasks, or experiment results. This is source-based qualitative review, not an independent correctness run or a performance measurement. No condition labels are inferred.

## Inventory: substantial structural agreement

Both implementations put stock balances and reservation records inside one `Inventory` object. Both expose the requested operations directly, share identifier/quantity validation, reject booleans as quantities, validate before state mutation, check request replay before checking available stock, preserve successful IDs after cancellation, and return newly constructed snapshot dictionaries. Dependencies are ordinary imports and method calls. Neither introduces persistence, I/O, concurrency machinery, a service locator, or a generic policy framework.

This is a strong match between the initial problem's invariant boundary and the code's state owner. A caller cannot alter the owner through a returned dictionary. Idempotency and availability changes are visibly coordinated within `reserve` and `cancel`.

The meaningful difference is the reservation representation:

- **inventory_x:** `_Reservation` is a mutable dataclass. Cancellation increments availability and changes `reservation.status` in place. This is a direct implementation of the current transition; a maintainer must preserve the convention that identity, SKU, and quantity are not subsequently modified.
- **inventory_y:** `_Reservation` is frozen and slotted. Cancellation creates a replacement with `dataclasses.replace`, then releases availability. The representation enforces normal attribute immutability and makes each reservation-state change an explicit replacement. It adds a standard-library operation that a maintainer must understand. The enclosing dictionaries and available-stock counter remain mutable, so record immutability alone does not enforce the inventory's cross-structure invariant.

Both maintain available stock as a stored counter alongside reservation records. This makes reads direct but creates a coordination obligation: future state transitions must preserve consistency between the counter and the records. That obligation is currently confined to one owner in both implementations. Their statement ordering differs, but neither implements a transaction mechanism; that is appropriate to the specified single-threaded, in-memory scope. It should not be described as a durability or concurrency guarantee.

The READMEs accurately explain replay, cancellation, defensive snapshots, and the excluded operational concerns. `inventory_y` also states ownership and immutable records explicitly; `inventory_x` explains the two internal dictionaries and retention of cancelled records.

The written tests in both implementations exercise observables, including failed reservations, replay after cancellation, conflicts, input rejection, and snapshot isolation. Their coverage emphases differ: `inventory_y` explicitly checks that cancelling an unknown ID does not consume it and that an invalid stock operation does not create a new SKU; `inventory_x` explicitly mutates the dictionary returned by initial creation as well as replay and lookup. These are specific test cases, not evidence of an overall quality ranking.

## Pricing: different placement of the same decisions

Both implementations use a pure `quote` function, a shared bounded-integer validator, integer arithmetic, and a newly returned result dictionary. Both validate item structure, exclude booleans, permit repeated SKUs and zero prices, avoid modifying inputs, apply discount after summing items, and exclude shipping from the tax base. There are no hidden clocks, mutable global state, external effects, or runtime dispatch mechanisms to recover.

The main distinction is the validation/aggregation boundary:

- **pricing_x:** `_subtotal_cents` owns item-container validation, item-field validation, and subtotal accumulation. `quote` owns option validation and the visible discount/tax/total calculation. The helper returns validated numeric values and production signatures have type annotations. This isolates the item-processing concept and lets `quote` express the formula directly, at the cost of following one helper to understand the entire input contract.
- **pricing_y:** `quote` contains container validation, option validation, item validation, accumulation, and final arithmetic in one source-level sequence. The integer validator checks values without returning them. Missing keys are checked explicitly, producing a diagnostic distinct from an invalid field value. The full behavior is available in one function, with no additional intermediate abstraction; future changes must preserve the distinction between input handling and monetary calculations within that function.

Neither choice is inherently superior for the supplied task. The helper in `pricing_x` compresses a coherent detail; the inline sequence in `pricing_y` removes a navigation step. Their economic value depends on actual changes rather than a preference for more or fewer functions. Option/container error precedence differs, but the initial task requires `ValueError` and does not prescribe precedence or exact messages.

Both written test suites cover large integers, percentage boundaries, input rejection, deterministic independent calls, non-mutation, and the shipping tax rule. `pricing_x` includes a particularly useful two-line, one-cent-each example proving that discount rounding occurs after aggregation; `pricing_y` lacks that explicit discriminator in its initial tests. The actual source in both implementations uses the required aggregate rounding. This is a difference in resistance to a particular future regression, not an observed defect.

## Interpretation limits

No initial-scope correctness defect was apparent from this reading. That statement is narrower than passing independent acceptance tests, which were not examined here.

The pairs share most important architectural decisions. Any later outcome difference should therefore be investigated at the level of the changed behavior, test selection, and the particular representation choice. This review does not support a claim that one pair member has a fundamentally different architecture, nor that any named principle caused a performance difference.

No verdict is based on file length, source volume, or test count. The useful qualitative differences are mutable versus replaced reservation records, inline versus extracted item processing, explicit diagnostics, and particular regression tests.
