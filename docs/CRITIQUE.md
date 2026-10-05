# Why AGENT might fail

AGENT is experimental source-design guidance for coding agents. Its hypothesis is that Atomic Context, Graph Explicitness, Economic Abstraction, Narrow Change Surface, and Testable Behavior can make source easier to implement and change correctly. The choices concern semantic decisions, dependencies, useful boundaries, state ownership, and observable effects. A plausible hypothesis is not an established result. This document states the strongest objections and the observations that should make the project revise or reject its guidance.

## 1. The principles may simply rename good engineering

Local reasoning, information hiding, explicit interfaces, cohesion, and executable constraints predate coding agents. Parnas described module boundaries in terms of responsibilities, comprehensibility, independent development, and accommodating change in 1972. [Original paper](https://doi.org/10.1145/361598.361623).

Recent prior art is close, too. The Context Minimization Principle evaluates designs through the acquisition cost of sufficient context for realistic correct modifications. Context Architecture binds repository claims to mechanisms that fail when those claims stop holding. These are substantive predecessors, not incidental references. [Context Minimization Principle](https://www.contextcost.dev/research/cmp/foundations/the-context-minimization-principle/); [Context Architecture](https://context-architecture.dev/).

AGENT's defensible contribution is a compact synthesis that tells agents how to choose source structure, accompanied by examples and an evaluation programme. The acronym establishes no originality. Neither object orientation nor familiar frameworks are intrinsically unsuitable for agents; well-understood interfaces can reduce uncertainty.

**Falsifier:** Excellent conventional architecture with ordinary tooling performs as well as AGENT-guided designs across matched tasks. Retain useful guidance, but withdraw claims of a distinct architectural advantage.

## 2. More explicit context can make agents worse

Exposing every internal detail can make a decision harder to understand. Many tiny functions can scatter a rule across files; a giant module can mix unrelated rules. An agent may already navigate familiar conventions cheaply. Additional instructions or maps consume attention, and stale descriptions can mislead.

The evidence is mixed. A September 2026 revision of an AGENTS.md evaluation reports no general improvement in task success and more than 20% higher average inference cost in its tested settings. Another study, across 10 repositories and 124 pull requests, reports lower median runtime and output-token consumption with context files. Different outcomes and experimental settings prevent a universal conclusion. Neither study evaluates the complete AGENT architecture. [Gloaguen et al., v3](https://arxiv.org/abs/2602.11988v3); [Lulla et al., v2](https://arxiv.org/abs/2601.20404v2).

Atomic Context therefore concerns coherent meaning in code and contracts. It does not require extra prose, a manifest, or a map. A boundary should expose what its caller needs while hiding stable implementation detail. Optional views should remain selective and current. Missing knowledge and insufficient implementation capability are different problems.

**Falsifier:** A supposedly clearer decomposition increases missed constraints or reading cost without improving correctness. Change the decomposition. If removing an optional context view preserves acceptance and lowers cost, remove it too.

## 3. The obvious metrics are easy to game

Fewer tokens can mean skipped constraints. Fewer edited files can mean an omitted consumer migration. Fewer graph hops can mean one enormous module. Shorter code can conceal removed functionality. An abstraction may save navigation today while making the next five changes harder.

Correctness and required operational properties must constrain the comparison. Record accepted outcomes, monetary cost, latency, tool execution, retries, failures, and metadata upkeep separately. Count every assigned attempt, including unsuccessful ones. Report unique tasks and repeated runs distinctly. A success-conditioned average hides the cost of failure.

**Falsifier:** A representation reduces tokens but increases missed regressions, recovery work, or lifecycle cost. It has not demonstrated an improvement for that task distribution. A cheaper failure is still a failure.

## 4. The graph can create false confidence

Imports reveal only part of a system. Relevant edges include schema compatibility, feature flags, generated code, event consumers, transaction boundaries, retries, permissions, caches, and deployment order. A constructor graph can be perfectly explicit while an event change breaks a consumer in another repository.

Static analysis approximates possible behavior. Runtime observations cover particular executions. Neither automatically yields a complete production graph. Even the absence of reported unknowns is ambiguous: the analyzer may lack support for an entire dependency class.

Express application-specific dependencies and effect order through inspectable calls, parameters, composition, and contracts. Where behavior depends on dynamic binding, expose the selection boundary and exercise it. If a supporting analyzer is used, state its scope and distinguish declared, derived, and observed relationships. A separate graph representation is optional.

**Falsifier:** Local changes repeatedly break undeclared schema, configuration, or effect dependencies. The graph has failed its intended maintenance scope, regardless of how clean its import diagram looks.

## 5. Local patches may have global consequences

A one-line serializer change may affect thousands of consumers. Several generated files may represent one coherent operation. Centralizing a policy reduces duplication but can create a shared bottleneck and a wider blast radius.

Parallel agents amplify this problem. Disjoint writes can conflict when one agent changes a contract another agent relied on. A clean Git merge establishes textual compatibility, not semantic compatibility. Test results from separate base revisions do not establish the combined candidate's behavior.

Narrow Change Surface must account for changed contracts, semantic read/write dependencies, consumers, migration sequencing, and recovery. Cross-cutting work belongs in evaluations. It cannot be excluded merely because locality is harder to achieve.

**Falsifier:** Independently accepted patches fail after integration, or routine changes require hidden synchronized edits. Revise ownership and coordination boundaries; rerun verification against the integrated candidate.

## 6. Testability can become self-confirmation

An agent can misunderstand a requirement, implement that misunderstanding, and write tests confirming it. A second agent may share the same error. Agreement and an impressive audit trail cannot establish that the intended behavior was delivered.

Testable Behavior can also be misapplied by mocking away concurrency, transactions, timing, or network effects. Passing explicit inputs helps reproduce a decision; it does not make a real adapter correct. Failure, retry, cancellation, and duplicate-delivery obligations need independently stated expectations and meaningful integration checks where relevant.

Evaluation must keep its acceptance criteria independent of the implementation agent's ability to change its own tests. That agent cannot obtain acceptance by silently narrowing the task or weakening an assertion. Selected fault injection can check whether a test detects the intended violation. It does not prove that all required behavior has been specified.

Larger autonomous workflows may also use revision-bound reports or receipts, as illustrated by the optional [verification profile](VERIFICATION-PROFILE.md). Hashes establish neither trustworthy authorship nor semantic correctness. These supporting tools are not requirements of the coding principles, and the local example does not implement a secured promotion service.

**Falsifier:** A candidate obtains acceptance by changing assertions, disabling discovery, replacing the grading contract, or replaying old evidence. That is a verification failure even if the candidate's own tests pass.

## 7. Present-day agent weaknesses may disappear

Better retrieval, longer effective context, improved models, or different harnesses could reduce the cost of navigating a familiar framework or deeper abstraction. A bespoke replacement chosen for one model may become unnecessary overhead with the next. Conversely, a well-designed contract can remain useful as the model changes; this also requires measurement.

The proposed properties should remain interoperable with ordinary languages and tools. No fixed file-size limit, universal token budget, or mandatory directory structure follows from the principles. Reevaluate mechanisms after major changes to models and harnesses.

**Falsifier:** Benefits disappear across model families or later versions while upkeep remains. Narrow the claim to the measured configuration or remove the mechanism.

## 8. A runnable example is not a productivity experiment

The refund fixture can illustrate explicit policy, invariant ownership, transaction boundaries, and selected checks that detect violations. Its supporting verification code can demonstrate stale-evidence handling. Neither demonstration establishes improved agent success or reduced implementation and maintenance cost. A deliberately tangled comparison implementation would not establish that either.

The completed [exploratory study](../experiments/README.md) compared agents writing libraries with ordinary instructions or AGENT guidance, then new agents implementing withheld changes. All four chains passed the finite acceptance suites; no acceptance-success advantage was observed. It evaluated the combined guidance and resulting code, without isolating each principle, measuring token costs, or demonstrating a controlled general advantage.

A credible experiment needs strong behavior-equivalent baselines, frozen acceptance criteria, fresh sessions, randomized conditions, repeated runs, and independent grading. Separate architecture, instructions, retrieval tooling, and verifier changes. Include sequential maintenance and data/configuration tasks. Publish failures, upkeep cost, raw measurements, and uncertainty.

Infrastructure also affects outcomes. Anthropic reports material coding-benchmark changes from resource configuration alone. Resource limits, tool versions, timeouts, concurrency, and network conditions therefore belong in the experimental record. [Infrastructure noise in agentic coding evaluations](https://www.anthropic.com/engineering/infrastructure-noise).

**Falsifier:** An apparent gain vanishes against a strong baseline, after accounting for infrastructure, or when the harness remains fixed. Attribute any surviving gain to the intervention actually measured.

## What would justify confidence?

Replicated gains on realistic tasks, across repositories and agent configurations, would justify bounded claims. Negative results are equally useful when they identify needless abstractions, misleading state ownership, ineffective tests, or costly structural rules. The completed [exploratory study](../experiments/README.md) is a first investigation; a controlled general advantage remains unproven.

Publicly attributable research and documentation can support specific claims. Unavailable or unverifiable leaks cannot establish effectiveness, priority, or provider endorsement. Stars measure attention and adoption, not correctness. AGENT earns technical credibility by making its claims testable and allowing the results to change the proposal.
