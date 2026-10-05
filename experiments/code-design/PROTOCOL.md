# Exploratory code-design and maintenance study

Executed 2026-10-05. This is a small feasibility study of source-code guidance, with substantial design and measurement limitations. The input record was frozen locally before generation; it was not preregistered in an independent public registry.

## Question and intervention

Can the AGENT coding guide influence useful source structure when an agent builds a library, and can a fresh agent extend that code without the original conversation?

The comparison is **ordinary engineering instructions versus the same task plus AGENT generation guidance**. The intervention is a document of coding principles, not a repository optimizer, special harness, generated context map, or new framework.

| Arm | Domain | Generation condition | Maintenance condition |
|---|---|---|---|
| inventory_x | Reservations | Ordinary | Neutral, fresh agent |
| inventory_y | Reservations | AGENT | Neutral, fresh agent |
| pricing_x | Pricing | AGENT | Neutral, fresh agent |
| pricing_y | Pricing | Ordinary | Neutral, fresh agent |

Arm letters were counterbalanced across the two domains, not randomly assigned. There is one generation and one follow-up per cell. The experimental unit is the generation/maintenance chain: four chains, eight agent episodes, two domains.

## Frozen inputs

The [registration](registration.json) records the design, assignment, timestamp, and SHA-256 of the four requirements and the [guide](guidance.md). The guide is the version supplied to the treatment builders, preserved exactly even if the repository's main guide later evolves.

- [Inventory initial task](tasks/inventory-initial.md): stock, reservation identity, replay, cancellation, validation, and defensive snapshots.
- [Inventory change](tasks/inventory-change.md): injected time, lazy expiration, renewal, and preservation of original replay identity.
- [Pricing initial task](tasks/pricing-initial.md): exact integer discounts, shipping, tax, input validation, and no mutation.
- [Pricing change](tasks/pricing-change.md): selective eligibility, caps, largest-remainder allocation, tax exemptions, and line breakdowns.

These requirements already specify strong behavioral contracts. They may reduce the room in which additional design guidance can help. They do not prescribe internal classes, helper boundaries, or directory structure.

## Agent instructions and procedure

The following describes the invocation instructions; it is a reconstruction of the common prompt structure, not a verbatim conversation export. The requirements and intervention document above are exact copies.

1. Each builder started as a fresh agent with no inherited conversation. It could read its initial task and its own output directory. Treatment builders could additionally read the frozen guide. Builders were told to produce correct, maintainable Python 3.11+ code, standard library only, with English tests and a README, and choose their own architecture without unrelated features.
2. Builders were told not to read future changes, other arms, evaluation files, or research discussions, and not to use the network or delegate. A soft approximately eight-minute completion request was used; it was not an enforced or measured budget.
3. All initial files were copied into source snapshots before maintenance. The common stage-1 evaluator ran after generation. Its results were not provided to the maintenance agents.
4. Each maintainer started fresh, with access instructions limited to its own initial code plus its domain's initial and change requirements. The neutral instruction was to implement the extension, preserve required initial behavior, update tests and documentation, and avoid unrelated features. Maintainers did not receive the guide or condition labels.
5. Final files were snapshotted before running the common evaluation. There was no repair using common acceptance-test feedback. Stage 2 includes stage 1; separate stage-1 runs on maintained code also record retained behavior.

All implementation agents inherited the session model configuration. The exact provider model snapshot, sampling parameters, token use, tool-read telemetry, and end-to-end duration were unavailable. Agent regeneration cannot be reproduced exactly from this record. We did not substitute guessed model names or estimated token savings.

The agents shared a filesystem and tools. Access separation was instruction-based, not an operating-system sandbox. Fresh context reduces conversation carryover but does not prove that prohibited files could not be accessed. Maintainers could infer a style from code or comments, so their condition is neutral instructions, not guaranteed blindness.

## Common evaluator

A separate fresh evaluator agent read only the four requirements. It delegated the pricing suite under the same restriction. The evaluator authors did not inspect candidate code or the intervention guide. Tests, runner, and protocol were frozen in [SHA256SUMS](evaluator/SHA256SUMS) before the first candidate evaluation. A separate reviewer checked their agreement with the written requirements without examining candidates or results; no blocking inconsistency was found.

Inventory has 13 initial and 16 extension test methods; pricing has 15 initial and 19 extension test methods. Parameterized subtests add cases, not independent observations. The common evaluator uses the public APIs, not candidate-authored tests or private architectural assertions.

Test coverage is finite. In particular, default use of `time.monotonic` is not directly checked, and invalid-input immutability paths are sampled rather than exhausted. Passing does not establish complete correctness, production readiness, concurrency safety, or superiority of a design. Tasks intentionally exclude persistence, real network effects, and concurrency.

## Source review

A separate reviewer inspected initial snapshots and initial requirements before seeing maintenance code. It then inspected both snapshots and the change requirements. It was instructed not to inspect the condition mapping, guide, or acceptance outcomes. The reviewer had earlier participated in conceptual analysis of AGENT; this was limited condition-blind source review, not an independent blinded research panel.

The reviews explain concrete structural decisions. They do not turn line counts, helper counts, or stylistic preferences into an architectural quality score.

## Artifacts and reproduction

All eight snapshots include source, self-tests, and README files. Files are unmodified copies excluding bytecode caches. [SNAPSHOT-SHA256SUMS](SNAPSHOT-SHA256SUMS) was generated after execution for publication integrity; unlike input registration, it is not a pre-execution record.

Observed JSON reports are preserved with their absolute `arm` paths replaced by repository-relative snapshot paths and JSON formatting normalized. No outcomes were edited. `duration_seconds` measures acceptance-suite execution only; it is not implementation time or agent performance.

The reproducer verifies frozen input, evaluator, and snapshot hashes, starts fresh Python processes with isolated bytecode caches, and compares test counts and outcomes with the recorded reports. It needs no network or third-party package. This is reproduction of source-level checks, not a replay of agent generation.

## Interpretation limits

There are no repeated generations, randomized assignment, measured costs, statistical inference, ablations, independent model families, larger applications, or long maintenance histories. Task and concept authors overlap. Strong task contracts and simple domains may create a ceiling. Guidance compliance was not assessed with a validated scoring system.

Equal results neither establish equivalence nor refute a benefit on harder tasks. They also provide no basis for promoting a general benefit. Future work should use the [larger protocol](../../benchmarks/PROTOCOL.md), including additional SOLID/contract/context-guidance baselines, repeated changes, and prospectively defined outcomes.
