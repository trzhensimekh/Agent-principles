# Agent legibility: the property AGENT aims to improve

**A system is legible to an agent when the agent can recover enough correct meaning to act on it without reconstructing the author's private context.** For coding work, that means locating behavior, understanding its constraints, predicting the consequences of a change, and verifying the resulting behavior.

This is an operational definition proposed by this project. The term **agent legibility** is already used in [OpenAI's harness-engineering account](https://openai.com/index/harness-engineering/), which describes making repository knowledge and application behavior accessible to agents. That account is engineering experience, not experimental validation of the five AGENT principles. The [prior-art review](PRIOR-ART.md) also credits Context Architecture and Context Minimization Principle for closely related ideas.

AGENT is the candidate architectural guidance. Legibility is the property we want that guidance to produce. Faster or more reliable task completion is a possible downstream benefit. Those three claims require different evidence.

## The agent's end-to-end reasoning path

```text
requirement
    -> relevant entry point and authoritative rule
    -> inputs, units, invariants, and failure semantics
    -> dependencies, state transitions, and external effects
    -> affected contracts and consumers
    -> observable result and independent checks
```

The source, types, tests, configuration, and interface contracts should make this path recoverable. No special graph format or mandatory trace document follows from it. An explanation written by an agent is evidence only to the extent that it matches the system's actual behavior.

For example, a fresh maintainer adding reservation renewal must discover that the original request's TTL defines replay identity while the current deadline defines expiration. A readable method name alone cannot communicate or enforce that distinction. Separate facts in the representation, a clear state owner, and boundary tests can make the distinction recoverable and challengeable.

## Four questions to measure separately

These dimensions are a proposed evaluation model, not four validated independent scales or a universal score.

| Question | Observable evidence | A misleading substitute |
|---|---|---|
| **Can the agent locate the relevant behavior?** | Whether it finds the authoritative rule and necessary consumers; search and reading before justified action | Small files, a directory diagram, or number of search hits |
| **Can it recover the semantics?** | Correct predictions about units, boundary cases, state transitions, failure and replay behavior, checked against an independent oracle | A fluent summary or confidence statement |
| **Can it predict change impact?** | Missed affected contracts, unnecessary edits, and regressions on previously withheld changes | Few changed lines or files |
| **Can it establish the outcome?** | Checks that exercise the required behavior and reject selected wrong implementations; explicit unknowns | A large test count or a passing self-authored happy path |

Measure correctness and effort together. An agent can read less because it understands a contract, because it guesses, or because it misses a dependency. Raw reading reduction cannot distinguish those cases. Conversely, reading more can prevent a costly regression.

Legibility is relational: it depends on the code, task, model, available tools, known conventions, and budget. A familiar framework can be more legible than a custom abstraction with fewer files. A design can help local policy changes and hinder cross-cutting changes. Report those scopes rather than declaring one globally legible architecture.

## How the five principles could produce legibility

| Principle | Proposed source mechanism | Failure the mechanism should reduce |
|---|---|---|
| Atomic Context | Coherent responsibility with its contract and assumptions | Missing a constraint dispersed across unrelated locations |
| Graph Explicitness | Inspectable dependencies, bindings, orchestration, and effects | Overlooking a consumer, hidden input, or side effect |
| Economic Abstraction | A boundary that hides useful complexity under a trustworthy contract | Reopening internals or navigating layers that do not reduce reasoning |
| Narrow Change Surface | Invariant-preserving ownership and private representation | Coordinating scattered writes or duplicating authoritative policy |
| Testable Behavior | Explicit inputs, observable effects, executable failure obligations | Being unable to reproduce or detect an incorrect decision |

These are causal hypotheses, not definitions that make AGENT true by construction. A design can follow the wording and still fail. A design can be legible without using the acronym. If an abstraction adds cost or a state owner obscures required coordination, the corresponding recommendation must be narrowed or rejected for that setting.

## A test that could support or challenge the concept

1. Freeze requirements and unseen changes before shaping the source. Include competent ordinary and established-design baselines.
2. Let fresh agents build code under the alternative guidance, using equivalent task knowledge, models, tools, and budgets. Separately compare behavior-equivalent structural variants when isolating a mechanism.
3. Give new agents independent tasks that probe discovery, semantics, impact, and verification. Score predictions against requirements and executions rather than the agent's own explanation. Accept alternate valid paths to evidence.
4. Evaluate actual edits with an independent acceptance suite. Keep mistakes, incomplete runs, regressions, and infrastructure failures visible.
5. Record navigation, cumulative input and output usage, time, retries, and upkeep. Compare effort at comparable success, retaining failed work in the accounting.
6. Repeat across tasks, change sequences, and model families. Report uncertainty and cases where the guidance makes work worse.

Separate diagnostic probes from the primary maintenance comparison: asking an agent to explain every dependency can itself change its search behavior and cost. Use a separate cohort, or count that probe as part of the intervention. Do not grade only agreement with one expected file list when another valid reasoning path exists.

See the [full evaluation protocol](../benchmarks/PROTOCOL.md) for controls and analysis. No static file-size threshold, architectural diagram, or linter can alone establish agent legibility.

## What the current experiment establishes

The [first exploratory study](../experiments/README.md) executed four generation/maintenance chains. All passed the finite common acceptance suites. It did not collect navigation, semantic-reconstruction, token, or agent-duration measurements. Consequently it establishes task completion within the checked scope, **not improved agent legibility**.

Condition-blind source reviews identify plausible mechanisms to investigate: immutable versus mutable reservation records, helper contracts versus inline phases, and the separation of original identity from current state. Those observations are useful hypotheses for a stronger experiment; they do not establish which version a fresh agent understood more easily.
