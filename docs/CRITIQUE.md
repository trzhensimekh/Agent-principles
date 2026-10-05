# Why AGENT might fail

AGENT is an experimental proposal for software maintained by coding agents. Its hypothesis is that addressable context, explicit dependencies, economical abstractions, bounded changes, and traceable verification can improve the cost and reliability of maintenance. A plausible hypothesis is not an established result. This document states the strongest objections and the observations that should make the project revise or reject its mechanisms.

## 1. The principles may simply rename good engineering

Local reasoning, information hiding, explicit interfaces, cohesion, and executable constraints predate coding agents. Parnas described module boundaries in terms of responsibilities, comprehensibility, independent development, and accommodating change in 1972. [Original paper](https://doi.org/10.1145/361598.361623).

Recent prior art is close, too. The Context Minimization Principle evaluates designs through the acquisition cost of sufficient context for realistic correct modifications. Context Architecture binds repository claims to mechanisms that fail when those claims stop holding. These are substantive predecessors, not incidental references. [Context Minimization Principle](https://www.contextcost.dev/research/cmp/foundations/the-context-minimization-principle/); [Context Architecture](https://context-architecture.dev/).

AGENT's defensible contribution is a proposed operational profile, executable examples, and an evaluation programme. The acronym establishes no originality. Neither object orientation nor familiar frameworks are intrinsically unsuitable for agents; well-understood interfaces can reduce uncertainty.

**Falsifier:** Excellent conventional architecture with ordinary tooling performs as well as the proposed mechanisms across matched tasks. Retain any useful tools or checklist, but withdraw claims of a distinct architectural advantage.

## 2. More explicit context can make agents worse

A repository map consumes attention and requires upkeep. An agent may already discover the relevant facts cheaply through language tools. Instructions can add work without improving the final patch. A stale description can be more misleading than no description.

The evidence is mixed. A September 2026 revision of an AGENTS.md evaluation reports no general improvement in task success and more than 20% higher average inference cost in its tested settings. Another study, across 10 repositories and 124 pull requests, reports lower median runtime and output-token consumption with context files. Different outcomes and experimental settings prevent a universal conclusion. Neither study evaluates the complete AGENT architecture. [Gloaguen et al., v3](https://arxiv.org/abs/2602.11988v3); [Lulla et al., v2](https://arxiv.org/abs/2601.20404v2).

Addressable Context therefore makes a new manifest optional. Task views should be selective, current, and derived from authoritative artifacts where practical. Missing knowledge and insufficient implementation capability are different problems.

**Falsifier:** Removing a context view preserves acceptance and lowers total cost. Delete or redesign that view; do not redefine every unsuccessful view as insufficiently “agent-native.”

## 3. The obvious metrics are easy to game

Fewer tokens can mean skipped constraints. Fewer edited files can mean an omitted consumer migration. Fewer graph hops can mean one enormous module. Shorter code can conceal removed functionality. An abstraction may save navigation today while making the next five changes harder.

Correctness and required operational properties must constrain the comparison. Record accepted outcomes, monetary cost, latency, tool execution, retries, failures, and metadata upkeep separately. Count every assigned attempt, including unsuccessful ones. Report unique tasks and repeated runs distinctly. A success-conditioned average hides the cost of failure.

**Falsifier:** A representation reduces tokens but increases missed regressions, recovery work, or lifecycle cost. It has not demonstrated an improvement for that task distribution. A cheaper failure is still a failure.

## 4. The graph can create false confidence

Imports reveal only part of a system. Relevant edges include schema compatibility, feature flags, generated code, event consumers, transaction boundaries, retries, permissions, caches, and deployment order. A constructor graph can be perfectly explicit while an event change breaks a consumer in another repository.

Static analysis approximates possible behavior. Runtime observations cover particular executions. Neither automatically yields a complete production graph. Even the absence of reported unknowns is ambiguous: the analyzer may lack support for an entire dependency class.

Expose the analysis scope and provenance of edges. Distinguish declarations, static derivations, runtime observations, and unsupported analysis. Query relevant slices rather than inserting the entire graph into context.

**Falsifier:** Local changes repeatedly break undeclared schema, configuration, or effect dependencies. The graph has failed its intended maintenance scope, regardless of how clean its import diagram looks.

## 5. Local patches may have global consequences

A one-line serializer change may affect thousands of consumers. Several generated files may represent one coherent operation. Centralizing a policy reduces duplication but can create a shared bottleneck and a wider blast radius.

Parallel agents amplify this problem. Disjoint writes can conflict when one agent changes a contract another agent relied on. A clean Git merge establishes textual compatibility, not semantic compatibility. Test results from separate base revisions do not establish the combined candidate's behavior.

Narrow Change Surface must account for changed contracts, semantic read/write dependencies, consumers, migration sequencing, and recovery. Cross-cutting work belongs in evaluations. It cannot be excluded merely because locality is harder to achieve.

**Falsifier:** Independently accepted patches fail after integration, or routine changes require hidden synchronized edits. Revise ownership and coordination boundaries; rerun verification against the integrated candidate.

## 6. Traceability can become self-certification

An agent can misunderstand a requirement, implement that misunderstanding, and write tests confirming it. A second agent may share the same error. Agreement and an impressive audit trail cannot establish that the intended behavior was delivered.

The acceptance policy must be independently controlled. It identifies mandatory claims, preserved constraints, allowed residual unknowns, and promotion scope. Required claims with failed, missing, or stale evidence block promotion. An implementation agent cannot obtain acceptance by silently narrowing the task, weakening a test, or moving a required property into a limitations list.

Receipts identify measured artifacts and observed results within a declared environment. Hashes do not authenticate their author or establish semantic correctness. Ordinary test logs are not formal proofs. The reference fixture deliberately demonstrates local checking and reproducibility; it does not implement a secured promotion service.

**Falsifier:** A candidate obtains acceptance by changing assertions, disabling discovery, replacing the grading contract, or replaying old evidence. That is a verification failure even if the candidate's own tests pass.

## 7. Present-day agent weaknesses may disappear

Better retrieval, longer effective context, improved models, or different harnesses could eliminate the benefit of a custom index. Familiar frameworks may become easier to use than a specialized agent architecture. A mechanism that pays for itself with one model may become unnecessary overhead with the next.

The proposed properties should remain interoperable with ordinary languages and tools. No fixed file-size limit, universal token budget, or mandatory directory structure follows from the principles. Reevaluate mechanisms after major changes to models and harnesses.

**Falsifier:** Benefits disappear across model families or later versions while upkeep remains. Narrow the claim to the measured configuration or remove the mechanism.

## 8. A runnable example is not a productivity experiment

The refund fixture can show that particular checks execute, selected violations are detected, and evidence becomes stale after input changes. It cannot show improved agent success or reduced maintenance cost. A deliberately tangled comparison implementation would not establish that either.

A credible experiment needs strong behavior-equivalent baselines, frozen acceptance criteria, fresh sessions, randomized conditions, repeated runs, and independent grading. Separate architecture, instructions, retrieval tooling, and verifier changes. Include sequential maintenance and data/configuration tasks. Publish failures, upkeep cost, raw measurements, and uncertainty.

Infrastructure also affects outcomes. Anthropic reports material coding-benchmark changes from resource configuration alone. Resource limits, tool versions, timeouts, concurrency, and network conditions therefore belong in the experimental record. [Infrastructure noise in agentic coding evaluations](https://www.anthropic.com/engineering/infrastructure-noise).

**Falsifier:** An apparent gain vanishes against a strong baseline, after accounting for infrastructure, or when the harness remains fixed. Attribute any surviving gain to the intervention actually measured.

## What would justify confidence?

Replicated gains on realistic tasks, across repositories and agent configurations, would justify bounded claims. Negative results are equally useful when they identify unnecessary metadata, unreliable checks, or ineffective structural rules. Until controlled trials exist, the performance hypothesis remains unmeasured.

Publicly attributable research and documentation can support specific claims. Unavailable or unverifiable leaks cannot establish effectiveness, priority, or provider endorsement. Stars measure attention and adoption, not correctness. AGENT earns technical credibility by making its claims testable and allowing the results to change the proposal.
