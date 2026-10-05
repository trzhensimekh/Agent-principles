# Prior art and positioning

Research cutoff: **2026-10-05**. Status: critical review supporting a proposal, not empirical validation of AGENT.

AGENT belongs to an existing line of work on modularity, context acquisition, contracts, and autonomous software development. Its proposed value is compact guidance for agents choosing how to express decisions, dependencies, abstractions, state ownership, and testable behavior in source code. Executable examples and experiments test that guidance. Neither the acronym nor the collection of principles establishes a new programming paradigm.

Two particularly close predecessors deserve explicit credit: **Sergio Azócar’s Context Architecture** and **Lianghui Zhang’s Context Minimization Principle (CMP)**. Together they cover much of the conceptual territory: repositories whose claims can be checked, and architecture evaluated by the cost of acquiring sufficient context for correct changes.

## Closest conceptual predecessors

### Context Architecture — Sergio Azócar

[Context Architecture](https://context-architecture.dev/) states that it was first published in June 2026; its author dates the term’s introduction to October 2025. The inspected specification covers domain-oriented structure, nearby context, explicit boundaries, discoverable capabilities, executable conventions, behavioral verification, and protection of the verification surface. It also discusses autonomous development and independent agent review.

This is substantial overlap with AGENT, especially A, G, N, and the executable obligations behind T. Connecting important architectural claims to failing checks is explicitly established here. AGENT v0.3 calls T **Testable Behavior**, emphasizing how source expresses reproducible decisions and observable effects. Agent-only maintenance and reviewer independence are also prior art.

The document is a design specification supported by engineering experience. It does not provide a controlled comparison demonstrating that its complete prescription improves maintenance outcomes. AGENT should credit its mechanisms and test their operational consequences rather than present them as new discoveries.

### Context Minimization Principle — Lianghui Zhang

Lianghui Zhang, also identified as Leric Zhang, frames design around the cost of obtaining enough context for realistic, correct modifications. [Reliable Coding Agents Need Better Codebases](https://www.contextcost.dev/research/cmp/start/reliable-coding-agents-need-better-codebases/), updated May 19, 2026, explains why agent traces make parts of that cost observable. It acknowledges dependence on the agent, tools, prompt, and task.

CMP directly precedes AGENT’s context-cost framing and Economic Abstraction principle. A boundary earns value when its contract lets a maintainer stop investigating implementation details. Context economics is therefore not an AGENT invention.

[Locality Principles: Designing Against Omission](https://www.contextcost.dev/research/cmp/principles/locality-principles/), also updated May 19, defines modification closure: the artifacts that must be considered together for a change. Locality concerns reaching that closure from legitimate starting points. Exhaustive mappings, registries, completeness tests, and explicit contracts are concrete mechanisms. This closely overlaps Atomic Context and Narrow Change Surface; proximity alone is insufficient.

[Architecture as Context Routing](https://www.contextcost.dev/research/cmp/principles/architecture-as-context-routing/), updated June 3, evaluates architectural styles against their expected modification patterns. Layers, feature slices, domain boundaries, and extension points can each help when they match the work. This supports treating AGENT as a lens across architectures rather than prescribing a universal directory tree.

These chapters supply a conceptual framework and examples. Whether particular transformations reduce cost without harming correctness remains an empirical question.

## Overlap map

| Existing work | Main contribution relevant to AGENT | Overlap | What AGENT must add to be useful |
|---|---|---|---|
| [Context Architecture](https://context-architecture.dev/) | Legible repositories with executable and protected claims | A, G, N, T | Concrete coding decisions and measured implementation/change outcomes |
| [CMP](https://www.contextcost.dev/research/cmp/start/reliable-coding-agents-need-better-codebases/) | Sufficient context and modification economics | A, E, N | Reproducible measurements across realistic task families |
| [OpenAI harness engineering](https://openai.com/index/harness-engineering/) | Agent-accessible repository knowledge, boundaries, and feedback | All five | Transferable examples and explicit limits of generalization |
| [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Selective context acquisition and long-task continuity | A, E | Repository-level hypotheses separated from harness effects |
| [Aider repository maps](https://aider.chat/docs/repomap.html) | Generated, budgeted views of source relationships | A, G | Evaluation of which representations help which changes |
| [ArchUnit](https://www.archunit.org/userguide/html/000_Index.html), [Bazel visibility](https://bazel.build/concepts/visibility) | Executable dependency constraints | G, supporting checks | Source-level guidance on boundaries, observable semantics, and their tradeoffs |
| [Agent-Native](https://www.agent-native.com/docs/what-is-agent-native/) | Shared application capabilities for agents and interfaces | Related operational interfaces | Clear separation between operating software and maintaining its source |

## Primary engineering evidence

### OpenAI: agent legibility and executable boundaries

Ryan Lopopolo’s [Harness engineering](https://openai.com/index/harness-engineering/), published February 11, 2026, reports an internal product developed through coding agents. Relevant practices include a short repository entry point, versioned knowledge, dependency enforcement, isolated runnable worktrees, and agent-accessible application diagnostics.

This provides practical evidence that the approach is implementable. It does not isolate the causal effect of code architecture from model capability, harness investment, task selection, or team practice. Its reported productivity estimates cannot be reused as expected AGENT gains. The article itself limits generalization beyond the particular environment.

### Anthropic: context, tools, and changing model capabilities

[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), September 29, 2025, motivates selective retrieval, progressive disclosure, compaction, persistent notes, and focused subagents. This supports managing sufficient context, but establishes no universal file-size ceiling or ideal module size.

[Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents), September 11, 2025, describes evaluation of tool names, descriptions, output detail, and errors. It recommends realistic tasks, held-out evaluation, and measurements including accuracy, calls, tokens, and runtime. Applying those findings to source-code abstractions is a hypothesis; tool ergonomics and code architecture are related but different interventions.

[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), November 26, 2025, documents continuity failures and premature completion claims. Progress artifacts, incremental work, reproducible setup, and browser verification helped in a web-application setting. A status record alone remains an assertion about completion.

[Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps), March 24, 2026, provides a critical qualification: model improvements made some earlier scaffolding unnecessary. Context resets and later sprint decomposition could be removed; evaluator value depended on task difficulty. The analogous design hypothesis is that a source abstraction should earn its cost with the agents and tasks actually using it; this transfer from harness design needs testing.

### Cursor and Aider: navigation is an independent variable

Cursor’s [Improving agent with semantic search](https://cursor.com/blog/semsearch), November 6, 2025, reports improved codebase question-answering accuracy in internal evaluations and improved code retention in online experiments. These concern retrieval tooling, not source architecture. A comparison that changes both cannot attribute the result to repository organization alone.

The [current Cursor search documentation](https://cursor.com/docs/agent/tools/search), inspected October 5, 2026, emphasizes local Instant Grep and an Explore subagent, and states that search does not store codebase embeddings. Historical and current descriptions should be dated separately. A principle about discoverability is more durable than a requirement to use one indexing method.

[Aider’s repository-map documentation](https://aider.chat/docs/repomap.html), inspected on the same date, describes selected signatures and definitions ranked through a dependency graph under a token budget. This demonstrates a working way to expose relationships progressively. A tool’s default budget is not an architectural law, and a generated static map cannot establish all runtime relationships.

## Established software engineering remains relevant

[Parnas’s 1972 modularity paper](https://doi.org/10.1145/361598.361623) treats modules as responsibility boundaries around design decisions. [Meyer’s Design by Contract](https://files.ifi.uzh.ch/rerg/amadeus/teaching/courses/ase_fs10/Meyer1992.pdf), 1992, formalizes caller/callee obligations and invariants in the object-oriented tradition. These are direct foundations for stopping at a trustworthy boundary and localizing changes. Their agent-specific economic interpretation is an inference; neither paper establishes AGENT outcomes.

[ArchUnit’s user guide](https://www.archunit.org/userguide/html/000_Index.html) documents dependency, layer, cycle, and module checks. [Bazel visibility](https://bazel.build/concepts/visibility) makes unauthorized dependency relationships fail during build analysis. Both were inspected October 5, 2026. They establish that machine-enforced architectural boundaries are available through existing tools. Their guarantees remain limited to the properties those tools analyze.

Aleksey Kladov’s [ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html), February 6, 2021, advocates a concise map of major components, boundaries, and invariants to reduce the effort of locating a change. Repository navigation was a maintenance problem before autonomous coding agents.

[AGENTS.md](https://agents.md/), inspected October 5, 2026, provides an established location for agent instructions and scoped commands. Reusing it avoids inventing a competing entry-point convention. The presence of that file proves neither instruction adherence nor improved task success; actual loading and execution depend on the harness.

AGENT does not require abandoning object-oriented, functional, domain-driven, or modular design. Those approaches supply candidate mechanisms. Their value should be judged against the resulting correctness, context acquisition, and change costs.

## Distinguishing maintenance from agent-operated products

Builder.io’s [Agent-Native documentation](https://www.agent-native.com/docs/what-is-agent-native/), inspected October 5, 2026, describes applications whose agents and interfaces share actions, data, and state. Its central concern is making product capabilities available through multiple interaction surfaces.

AGENT’s primary subject is source code written and changed by coding agents. An ordinary application can apply AGENT without containing an AI feature. Conversely, exposing application tools does not automatically make its implementation easy for another agent to understand. The two concerns can share typed contracts and inspectable effects without being identical.

## Defensible positioning and research boundary

**AGENT is an experimental synthesis of five software-design principles for AI coding agents.** Its subject is the code's structure and observable behavior. Its credibility depends on useful coding guidance, transparent attribution, and published results, including failures. Manifests, maps, and receipts are optional supporting mechanisms described separately in the [verification profile](VERIFICATION-PROFILE.md); they are not prerequisites for applying the principles.

The architectural hypothesis is that these coding decisions can reduce reconstruction during implementation and future changes while preserving independently checked behavior. Testing it requires equivalent requirements, realistic unseen changes, a competent conventional baseline, repeated trials, and fixed or explicitly varied models and harnesses. Navigation, implementation, verification, failures, and infrastructure cost must be distinguished. Lower token use on unsuccessful tasks is not evidence of better architecture. The completed [exploratory study](../experiments/README.md) found no acceptance-success difference across its four chains. It did not measure token costs, and a controlled general advantage remains unproven.

Neither this review nor a passing demonstration establishes universal superiority, complete verification, an optimal layout, or a guaranteed reduction in tokens. Claims of being the first architecture for agents, replacing SOLID, or inventing context-cost analysis would exceed the evidence.

This review uses public primary documentation and author-maintained specifications. Unauthenticated leaks do not establish product behavior or engineering efficacy and do not support the proposal. Live documentation can change; evaluations should record tool versions and dates alongside repository commits.
