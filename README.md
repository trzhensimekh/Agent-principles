# AGENT Principles

**Five software-design principles for AI coding agents.**

Write code the next agent can understand, change, and verify without inheriting your conversation.

[Agent legibility](docs/LEGIBILITY.md) · [The principles](SPECIFICATION.md) · [Coding guide](GUIDE.md) · [Experiments](experiments/README.md) · [Research](RESEARCH.md)

**Agent legibility is the goal; AGENT is a proposed set of design principles for achieving it.** A legible system lets a fresh agent locate a rule, recover its meaning and constraints, trace the consequences of a change, and verify the outcome from the source and its contracts. The term is established in [OpenAI's engineering account](https://openai.com/index/harness-engineering/); this project investigates which code-design decisions improve it.

AGENT is design guidance for agents writing source code: where to put a rule, how to expose a dependency, when to introduce an abstraction, who owns state, and how to make behavior testable. It applies to ordinary applications, libraries, and services.

## The five principles

| | Principle | Instruction to the agent writing code |
|---|---|---|
| **A** | **Atomic Context** | Keep a decision's inputs, rules, invariants, and failures understandable together. |
| **G** | **Graph Explicitness** | Make dependencies and the path from input to effects visible in the source. |
| **E** | **Economic Abstraction** | Introduce abstractions that remove more reasoning than their indirection adds. |
| **N** | **Narrow Change Surface** | Give state and invariants clear owners; keep expected changes behind their boundaries. |
| **T** | **Testable Behavior** | Make decisions reproducible and effects observable, including failures and retries. |

**Design around a semantic responsibility: a decision, invariant, algorithm, or protocol.** A useful boundary lets the next agent stop reading because its contract answers what matters.

## What changes in the code?

| Design choice | AGENT guidance |
|---|---|
| Where does a business rule live? | In one named owner, with its units, boundary conditions, and failure semantics. |
| How does a workflow execute? | Through explicit orchestration and inspectable bindings. |
| Should this become a framework or interface? | Only when its contract hides useful complexity or isolates genuine variation. |
| Who can mutate shared state? | Operations that own and preserve its invariants. |
| How does time, storage, or the network enter? | Through explicit inputs or effect boundaries that can be exercised. |
| What happens after retries, partial failure, or cancellation? | The behavior is part of the operation's contract and tests. |

For example, expose an invariant-preserving operation:

```python
# The caller coordinates mutable state and must rediscover its rules.
available = inventory.read_available(sku)
if available >= quantity:
    inventory.write_available(sku, available - quantity)

# The owner enforces the reservation contract.
reservation = inventory.reserve(request_id, sku, quantity)
```

The second shape helps only if `reserve` actually owns validation, state transitions, and the required idempotency/concurrency semantics. Good names do not compensate for a broken contract. The [full principles](SPECIFICATION.md) explain these obligations and their tradeoffs.

## Use it while coding

Give an agent the compact [GUIDE.md](GUIDE.md) alongside the task. It should apply the rules directly in source code using ordinary functions, objects, modules, and familiar frameworks. No AGENT package, repository map, manifest, or receipt format is required.

Start with the behavior and its invariant. Choose a cohesive owner. Expose the relevant dependencies. Introduce boundaries that let callers stop knowing details. Keep mutable state under controlled transitions. Make the outcomes and important failure paths executable.

The [design decisions](docs/DESIGN-DECISIONS.md) cover modules, interfaces, inheritance, frameworks, asynchronous effects, and distributed state. AGENT supplies criteria for those choices, not one mandatory directory structure.

## Test the principles against real agent work

The experiment in this repository compares fresh agents building the same libraries with ordinary instructions or AGENT guidance, followed by new agents implementing previously withheld changes. Common acceptance tests evaluate the resulting code. Read the [experiment, source snapshots, and results](experiments/README.md).

All four exploratory generation/maintenance chains passed the finite acceptance suites. **No advantage over ordinary instructions was observed in acceptance success; navigation, semantic reconstruction, token use, and agent duration were not measured.** This checks task completion, not improved legibility. Source review found substantial architectural overlap. Larger comparisons should follow the [evaluation protocol](benchmarks/PROTOCOL.md), include competent baselines and repeated changes, and count failed work as well as successful work.

An additional [runnable reference](examples/reference/README.md) illustrates explicit policy, state ownership, transaction boundaries, and executable checks. Its verification tools are supporting examples; they are not the product or a requirement for using the principles.

## Why another set of design principles?

SOLID addresses object responsibilities, substitution, interfaces, and dependencies. AGENT emphasizes the work a fresh coding agent must perform to reconstruct a decision and change it correctly under limited active context. It combines established design ideas around that maintainer, including the costs of indirection, hidden state, implicit effects, and incomplete feedback.

The proposal builds on information hiding and contracts, [Context Architecture](https://context-architecture.dev/), and [Lianghui Zhang's Context Minimization Principle](https://www.contextcost.dev/research/cmp/start/reliable-coding-agents-need-better-codebases/). The [prior-art review](docs/PRIOR-ART.md) credits substantial overlap. The [research review](RESEARCH.md) separates supporting evidence from untested hypotheses.

**v0.3 · Experimental design principles.** Counterexamples and competing designs are welcome. See [critique](docs/CRITIQUE.md), [contributing](CONTRIBUTING.md), and [changelog](CHANGELOG.md).

## License

Copyright © 2026 trzhensimekh and contributors.

Prose: [CC BY 4.0](LICENSE). Original source, examples, and tooling: [MIT](LICENSE-CODE). Referenced third-party works retain their licenses.
