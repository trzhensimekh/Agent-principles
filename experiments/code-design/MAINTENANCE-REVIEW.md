# Condition-blind review of maintenance changes

## Scope

Reviewed source diffs, tests, and READMEs in `snapshots/initial` and `snapshots/maintained` for `inventory_x`, `inventory_y`, `pricing_x`, and `pricing_y`, against the initial and change tasks in `tasks`. Condition labels, guidance, registration, execution results, and experiment reports were not read. This is a qualitative source review, not a performance comparison or a new acceptance-test run. No condition labels are inferred.

## Inventory: both preserve the original ownership boundary

Both implementations extend the existing `Inventory` owner rather than introducing a scheduler, separate reservation service, or generic lifecycle framework. The owner still coordinates free-stock counters and retained reservation records. A new `_expire(now)` method performs expiration and releases units; each specified observing method invokes it after validating arguments. `stock` does not invoke it, consistent with the explicitly listed observation points in the change task.

Both separate two facts that maintenance could easily conflate: `original_ttl` belongs to the idempotency signature, while `expires_at` is mutable lifecycle state. Renewal changes the deadline without changing replay identity. Both compare TTLs numerically and preserve terminal records. This is a concrete example of assigning distinct meanings to fields even when both initially derive from the same input.

The clock is injected and defaults to `time.monotonic`. `reserve` and `renew` each acquire one instant, use it for expiration, and calculate any new deadline from that same instant. This avoids an implicit sequencing dependency on multiple clock reads. Clock injection and the default were required by the maintenance task itself, so their appearance cannot be attributed to an unknown experimental condition.

### inventory_x

The original mutable dataclass remains mutable. Expiration and cancellation change `status` in place; renewal changes `expires_at` in place. State transition code is direct, and the same object continues to represent the reservation. Snapshot generation still separates public dictionaries from that object.

This preserves the initial implementation's principal convention: identity, SKU, quantity, and original TTL should remain unchanged after creation, even though the representation permits assignment. The current transition methods respect that convention. A future maintainer must distinguish identity fields from lifecycle fields when editing this record.

The TTL validator has an `optional` parameter, allowing `None` for `reserve` while rejecting it for `renew`. This centralizes the shared numeric rule, with the difference between the two public contracts expressed at the call site.

### inventory_y

The original frozen, slotted record also survives maintenance. Expiration, cancellation, and renewal replace records through `dataclasses.replace`. This makes the state transition an explicit construction of a new record while retaining unchanged fields. Normal attribute mutation cannot accidentally alter the original request signature.

The enclosing owner still needs to coordinate replacement with stock-counter changes; record immutability does not prove their joint invariant. The TTL validator always requires a number, and `reserve` alone handles the permitted `None` case before invoking it. This keeps the validator's contract uniform and places optionality in the public operation.

### Shared coupling and evidence limits

Expiration changes ostensibly observational operations such as `available` and `get_reservation` into state-updating operations. The implementation makes this visible through `_expire`, and the READMEs explain lazy expiration. Future public observers must preserve this convention or risk inconsistent lifecycle views. Both added tests enter through each required observer without first invoking another method that could conceal a missing expiration step.

Both expiration implementations scan retained reservation history, including terminal records. This avoids a second deadline index and its consistency obligations, but work per observation grows with retained history. The documents acknowledge scanning and lifetime retention. This is a structural tradeoff, not a measured latency result or a defect against the supplied scope.

Both test additions cover boundary expiry, release-once behavior, renewal, original-signature conflicts, invalid TTLs, and defensive snapshots using a controllable clock. `inventory_y` additionally asserts one clock call per `reserve`/`renew`; `inventory_x` implements that behavior without the corresponding explicit call-count assertion.

A shared numeric boundary deserves attention in a stronger specification: accepting finite clock values and TTLs does not ensure their sum is representable as a finite float. Both compute `now + ttl_seconds` directly after input validation. Float overflow and very large integer/float combinations are therefore unaddressed representation risks; this review did not execute such cases or reinterpret the frozen trial's acceptance rules.

## Pricing: the original extraction distinction becomes more consequential

Both implementations remain deterministic functions with no external effects or persistent state. Each validates the new boolean flags and cap, preserves row order and duplicate SKUs, uses integer `divmod` for proportional allocation, breaks remainder ties by input position, and calculates tax once over the aggregate taxable net. The allocation algorithm and tie rule were specified by the task, so their shared presence is not evidence of a design-condition effect.

### pricing_x

The original `_subtotal_cents` boundary evolves into `_validated_rows`, which returns fresh tuples containing SKU, subtotal, discountability, and taxability. A new `_allocate_discount(weights, discount)` isolates largest-remainder allocation. `quote` composes validation, discount calculation/capping, allocation, row construction, and tax calculation.

This gives allocation a narrow numeric input/output boundary: it need not know SKU names, tax flags, shipping, or caller dictionaries. A maintainer changing allocation can inspect that algorithm separately. Understanding the entire quote requires following the validation and allocation calls and their contracts.

The private contracts carry assumptions worth preserving: allocation expects nonnegative weights and a discount bounded by their sum; its output must remain aligned with the row sequence. `quote` currently establishes these conditions. Tuple positions distinguish two adjacent boolean fields, and `zip(rows, allocations)` relies on equal lengths. These are representation and coordination obligations, not observed errors. A named row type or explicit length assertion would be a possible future tradeoff, not an automatic requirement.

### pricing_y

The implementation retains the original inline organization. `quote` validates each item while constructing fresh output-shaped line dictionaries, tracks eligible input indices, calculates the total discount, mutates those fresh lines with allocated discounts, then derives line nets and the tax base. Only primitive validators are extracted.

The full policy sequence is visible in one function, and there is no separate internal row schema to translate. The output representation also serves as a working representation. Consequently, allocation and taxation depend directly on output dictionary keys and on the meaning of fields at each phase: `net_cents` initially means subtotal and later means subtotal after allocation. Future edits must preserve that phase ordering and correspondence between eligible indices and lines. These mutations do not escape into caller inputs.

### Test adaptation and surviving distinctions

Both implementations add tests for remainder ranking, input-order ties, selective tax consequences, zero eligibility, caps, large integers, strict flags, and allocation conservation. The earlier difference in an explicit aggregate-rounding regression does not justify a broad maintained-state coverage ranking: both now contain discriminating multi-row allocation and aggregate-tax examples.

`pricing_x` introduces an assertion helper to preserve existing monetary expectations while checking the extended output shape; separate assertions cover line details. `pricing_y` extends original full-dictionary expectations with `lines` and adds a separate selective-pricing test class. Both approaches retain the old monetary contract while accepting the required output extension. Neither test organization establishes superiority by itself.

## What this review supports

The initial representation choices persist: mutable versus replaced reservation records, and extracted versus inline pricing processing. Maintenance elaborates those choices rather than replacing them. Both inventory variants keep the lifecycle invariant inside one owner; both pricing variants preserve purity and explicit arithmetic.

The substantive comparison is about where assumptions live. `pricing_x` places assumptions at private helper boundaries and positional row mappings; `pricing_y` places them in an ordered sequence of mutable intermediate fields. `inventory_x` uses conventions around a mutable record; `inventory_y` additionally uses record immutability. Each has a concrete reading and modification obligation.

These observations provide mechanisms to investigate in larger experiments. They do not establish which implementation was easier for an agent, which used fewer tokens, or which instruction caused a change. No conclusion is based on source length, file count, or test count, and no new correctness result is claimed.
