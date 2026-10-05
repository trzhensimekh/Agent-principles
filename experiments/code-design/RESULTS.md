# Results: code design followed by fresh maintenance

**No acceptance-test advantage was observed for AGENT in this study.** All four initial implementations and all four maintained implementations passed the common requirements suites. The tasks and sample are too small to establish equivalence, superiority, or a general performance effect.

## Observed outcomes

| Chain | Generation condition | Initial suite | Initial behavior after change | Full extended suite |
|---|---|---|---|---|
| inventory_x | Ordinary | 13/13 | 13/13 | 29/29 |
| inventory_y | AGENT | 13/13 | 13/13 | 29/29 |
| pricing_x | AGENT | 15/15 | 15/15 | 34/34 |
| pricing_y | Ordinary | 15/15 | 15/15 | 34/34 |

Every reported run had zero failures, errors, skips, expected failures, or unexpected successes. The full extended suite includes initial tests; columns are not independent samples. There are four generation/maintenance chains, not one observation per passing assertion. The [JSON reports](results/) contain the recorded results and evaluator hashes.

Candidate-authored tests are retained as source artifacts. Their varying counts are not a measure of comparative correctness or test quality.

## What the code actually shows

The [initial review](INITIAL-REVIEW.md) found substantial agreement across conditions. Both inventory versions use one state owner, explicit operations, shared validation, replay checks, and defensive snapshots. Both pricing versions use pure calculations, explicit parameters, exact integer arithmetic, and no input mutation.

Concrete differences remained: inventory_x uses mutable reservation records while inventory_y uses frozen records and replacement; pricing_x initially extracts item validation/aggregation while pricing_y keeps those operations inline. Those choices have tradeoffs. Immutability does not by itself preserve the inventory's cross-structure invariant, and one extra helper is not automatically cheaper or more expensive for a maintainer.

The [maintenance review](MAINTENANCE-REVIEW.md) examines what happened to those choices under expiration/renewal and allocation/tax changes. These are qualitative source observations, not measured effects attributable to the guide.

That review also identified a shared, untested representation risk: finite clock and TTL inputs need not produce a representable finite floating-point deadline. The frozen tests were not expanded after seeing this observation. It is a follow-up lead, not an executed failure result or a difference between conditions; numeric bounds and overflow semantics deserve an explicit contract in a stronger task.

## Conclusions warranted by this run

- The intervention was usable in actual code generation, and fresh agents successfully extended the resulting libraries within the acceptance scope.
- Competent ordinary instructions also produced cohesive, explicit, maintainable-enough code for these changes.
- This task set did not discriminate the conditions by initial or maintenance acceptance success.
- Architectural differences can be inspected in full rather than inferred from a principles checklist.

The run does **not** show lower token usage, faster maintenance, greater correctness, fewer agent mistakes, or a generally better architecture. None of the first three were demonstrated comparatively; token usage and agent duration were not measured at all. There is no sound effect-size estimate from this design.

Navigation and semantic reconstruction were not instrumented either. Consequently this study does not directly measure [agent legibility](../../docs/LEGIBILITY.md), the target property behind the principles.

## Implications for the concept

AGENT should remain a testable proposal for coding guidance. Its public claim is the set of design decisions and the reasoning behind them, with evidence and counterexamples available. It should not claim that ordinary code is inherently unreadable to agents or that adding the acronym produces improvement.

The next study should introduce longer change sequences, multiple consumers, configuration/effects, and real competing abstractions; retain strict behavior requirements; compare against equally concise established-design guidance; repeat generations; and capture actual navigation, errors, tokens, and total cost. Those are prospective choices, not a reason to relabel this result as a win.

See [protocol and limitations](PROTOCOL.md) and [reproduction instructions](../README.md).
