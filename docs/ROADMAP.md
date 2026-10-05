# Research and development roadmap

The product is a useful set of code-design principles for autonomous coding agents. Tools and experiments serve that goal.

The target property is [agent legibility](LEGIBILITY.md). Measure how accurately and efficiently a fresh agent locates behavior, reconstructs semantics, predicts impact, and verifies an outcome. Task success is necessary evidence of useful work but does not by itself measure legibility.

## Current: make the guidance concrete

- Express each principle as a choice an agent makes while writing code.
- Include state ownership, explicit effects, contracts, failure semantics, and tradeoffs.
- Provide a compact generation guide without a required framework or repository layout.
- Compare actual agent-generated code and subsequent changes, preserving unsuccessful results.

The first [exploratory study](../experiments/README.md) covers two small domains and one follow-up change per implementation. Its value is finding concrete design differences and counterexamples. It cannot establish broad efficiency gains.

## Next: improve discrimination

If competent agents succeed equally in both conditions, increase task diversity rather than manufacturing a weak baseline. Investigate:

- multi-module workflows with configuration-selected behavior;
- asynchronous state, duplicate delivery, cancellation, and recovery;
- cross-cutting schema and protocol changes;
- several successive modifications by fresh agents;
- familiar versus unfamiliar framework conventions;
- different task families that challenge the original design's assumptions.

Freeze tasks and acceptance criteria before optimizing a principle. Separate ongoing instruction effects from properties of the generated code: neutral maintainers are useful for the latter question.

## Then: quantify transfer and economics

Use multiple independently developed model families, repeated trials, and more repositories/languages. Collect provider usage where available. Measure correctness, cost including failures, maintenance effort, and retention across a change sequence. Follow the [evaluation protocol](../benchmarks/PROTOCOL.md).

Test principles individually and in combination. A useful mnemonic can contain a redundant or misleading rule; revise the rule when experiments expose it. Numerical targets are experimental preferences, not universal laws.

## Publication strategy

Lead with clear code-design guidance, concrete examples, and reproducible experiments. Keep historical versions and contrary results available. Invite counterexamples and alternative designs that perform better.

A short walkthrough showing a fresh agent modifying unfamiliar code can communicate the value when supported by real artifacts. Stars may follow useful guidance and honest demonstrations; they are not evidence of architectural quality or a promised result.
