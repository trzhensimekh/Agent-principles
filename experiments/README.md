# Experiments with AGENT code-design guidance

**The first exploratory study found no acceptance-test advantage for AGENT.** All four generated libraries and all four fresh-maintainer extensions passed the common suites. Source review found considerable architectural overlap between conditions.

This repository separates observed results from the proposed benefit. Guidance must earn its place through better agent work; an appealing acronym is not evidence.

## Completed study

[Code design and fresh maintenance, 2026-10-05](code-design/RESULTS.md): two domains, ordinary versus AGENT generation instructions, and a new neutral maintainer for each implementation. Four generation episodes plus four maintenance episodes form **four dependent chains**, with one chain per domain and condition. They are not eight independent samples.

| Domain | Ordinary: initial → extended | AGENT: initial → extended |
|---|---|---|
| In-memory reservations | 13/13 → 29/29 | 13/13 → 29/29 |
| Integer price calculation | 15/15 → 34/34 | 15/15 → 34/34 |

The values count test methods, not independent tasks. The extended suite includes the initial suite.

- [Protocol and limitations](code-design/PROTOCOL.md)
- [Frozen requirements](code-design/tasks/), [generation guidance](code-design/guidance.md), and [input registration](code-design/registration.json)
- [Initial code](code-design/snapshots/initial/) and [maintained code](code-design/snapshots/maintained/), including each agent's tests and README
- [Independent common evaluator](code-design/evaluator/) and [observed reports](code-design/results/)
- [Initial source review](code-design/INITIAL-REVIEW.md) and [maintenance source review](code-design/MAINTENANCE-REVIEW.md)

Run the recorded checks from the repository root:

```sh
python experiments/code-design/reproduce.py
```

This reproduces acceptance results on the committed source snapshots. It does not regenerate the agent episodes or establish repeatability across models.

## What this changes

The study supports feasibility: agents can apply the compact guidance to real implementation work, and fresh agents can extend those implementations. Ordinary instructions worked equally well within the checked scope. No observed token, cost, speed, reliability, or general architectural advantage is claimed.

The next experiment needs harder, varied change sequences and stronger discrimination between candidate designs. The [larger evaluation protocol](../benchmarks/PROTOCOL.md) describes repeated tasks, competent baselines, telemetry, and independent evaluation. It is a proposed protocol, not an account of what this small study executed.
