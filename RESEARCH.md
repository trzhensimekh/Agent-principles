# Research basis and open questions

**Evidence reviewed: 2026-10-05 · Status: critical research synthesis and experimental proposal**

AGENT investigates a concrete engineering question: can software be organized so that autonomous coding agents complete correct changes with less discovery, inference, coordination, and verification cost, while remaining effective across future changes?

The evidence supports investigating that question. It does not establish the superiority of AGENT, the obsolescence of object-oriented programming, or a universal architecture for agents. This repository provides an [experimental specification](SPECIFICATION.md), explains its [relationship to prior art](docs/PRIOR-ART.md), and proposes a [controlled evaluation protocol](benchmarks/PROTOCOL.md). Its executable example demonstrates selected mechanisms; it is not a completed agent-performance experiment.

## 1. Research method and limits

This review used targeted public-web searches completed on October 5, 2026. Search families covered repository-level coding benchmarks, agent navigation and retrieval, context-window degradation, repository instruction files, architecture quality, tool interfaces, and iterative code maintenance. Search results served as discovery aids. Claims below were checked against primary papers, their available full text, official publication records, or the original technical report. We inspected experimental setups, ablations, version histories, and limitations where available.

Selection favored work that measures an observable outcome, exposes an evaluation mechanism, or supplies counterevidence to a plausible AGENT claim. Historical studies are retained when they clarify the mechanism or experimental design. Recent preprints are included for relevance, with their status visible. Secondary summaries, unverified leaks, popularity, and product claims are not treated as experimental evidence.

This is a focused synthesis, **not an exhaustive systematic review or a meta-analysis**. We did not reproduce the external experiments. Benchmark populations, costs, models, and outcome definitions differ, so their numbers must not be pooled. “Latest” means the version inspected at this review date; linked versioned papers preserve that scope. An arXiv entry marked “preprint version” below means that this review relies on that version, without asserting an unverified publication status elsewhere.

Evidence has three different roles here: an experimental intervention can support a scoped causal claim; repository mining can reveal associations or estimate effects under identification assumptions; engineering inference proposes a mechanism that still needs direct testing. None automatically transfers to a different model, harness, language, or task distribution.

## 2. Primary-source evidence

Numbers describe the cited experiments, not current leaderboards. Each row states both the useful result and its practical limit.

| ID | Source and status | Observed result | Interpretation and limit |
|---|---|---|---|
| R1 | [SWE-bench](https://arxiv.org/html/2310.06770v3), Jimenez et al.; ICLR 2024, v3 dated 2024-11-11 | Establishes executable issue-resolution evaluation using 2,294 tasks from twelve Python repositories. Tasks require changes within existing systems rather than isolated function synthesis. | A useful task-and-oracle pattern. Its original model scores are historical; public Python issues and snapshot repair do not represent all software maintenance. |
| R2 | [SWE-agent](https://arxiv.org/html/2405.15793v3), Yang et al.; NeurIPS 2024, v3 dated 2024-11-11 | Interface ablations on 300 SWE-bench Lite tasks report a 10.7-percentage-point improvement over a default-shell agent. Search, bounded views, edits, feedback, and guardrails form the intervention. | Strong motivation to design for an agent's interaction costs. The manipulated variable is the interface, not the source architecture; older-model results cannot validate AGENT. |
| R3 | [Agentless](https://arxiv.org/html/2407.01489v2), Xia et al.; preprint version dated 2024-10-29 | A localization–repair–validation pipeline reached 32% on SWE-bench Lite at a reported $0.70 average cost. Component ablations examine localization and validation. | Structured discovery can be competitive without elaborate autonomy. This is a historical Python repair result, not a universal argument against agents, frameworks, or complex workflows. |
| R4 | [RepoGraph](https://arxiv.org/html/2410.14684v2), Ouyang et al.; ICLR 2025, v2 dated 2025-03-18 | Adding graph retrieval improved several systems. In one ablation, one-hop flattened context resolved 29.67% versus 26.00% for larger two-hop flattened context. | Supports testing queryable relationships and bounded retrieval. It does not establish that more graph context is better, or that rewriting a repository produces the same effect. |
| R5 | [NoLiMa](https://arxiv.org/html/2502.05167v3), Modarressi et al.; ICML 2025, v3 dated 2025-07-09 | In controlled retrieval with little lexical overlap, eleven of thirteen models fell below half their short-context baseline at 32K tokens. | Advertised context capacity is not demonstrated comprehension capacity. These are synthetic retrieval tasks, not autonomous code changes; no universal file-size or token limit follows. |
| R6 | [Context Rot](https://www.trychroma.com/research/context-rot), Hong et al.; Chroma vendor technical report, 2025-07-14 | Controlled tasks across eighteen models show nonuniform performance as input grows; the report also compares focused and full conversational contexts. Replication code is public. | Corroborates concern about irrelevant context. It is a vendor report using synthetic and QA tasks; it does not measure source architecture or prove that every shorter prompt is better. |
| R7 | [Coding Agents are Effective Long-Context Processors](https://arxiv.org/html/2603.20432v1), Cao et al.; preprint, 2026-03-20 | Coding agents use files and executable tools for large-corpus QA. A 100-example structure ablation scored 89% with separate files versus 83% with a single JSON dictionary, without a retriever. | External, navigable evidence can exceed a model's active context. Text-processing tasks, sampled datasets, and limited alternative-agent checks constrain transfer to codebase maintenance. |
| R8 | [Evaluating AGENTS.md](https://arxiv.org/html/2602.11988v3), Gloaguen et al.; revised preprint, 2026-09-29 | Across four model/agent combinations, context files did not significantly improve resolution versus no context. Generated files increased costs about 20–23%. The new dataset is called CTXbench in this version. | Direct counterevidence to assuming that added repository instructions improve performance. Python task resolution does not measure every convention, security property, or long-term effect. Earlier versions used stronger framing. |
| R9 | [A Few Pages of Markdown](https://arxiv.org/html/2608.25241v2), Denisov-Blanch et al.; preprint, 2026-09-14 | In an adoption-panel analysis, configured agent-first repositories had smaller cognitive-complexity increases, approximately +27% versus +53%. The separate RAMP instrument study covers 441 repositories. | Configuration maturity is observational. Reverse causality, engineering discipline, model capability, and usage intensity can explain part of the association. It does not show that adding Markdown causally halves technical debt. |
| R10 | [SWE-Explore](https://arxiv.org/html/2606.07297v1), Zhang et al.; preprint, 2026-06-05 | Evaluates ranked code regions under a line budget on 848 issues, 203 repositories, and ten languages. Restricted-context repair experiments connect exploration metrics with downstream behavior. | Useful for measuring evidence acquisition separately from patching. Relevant-context labels derive from successful agent traces; they exclude wholly unsolved tasks and cannot enumerate every valid solution path. |
| R11 | [Agent Retrieval Bench](https://arxiv.org/html/2607.24882v1), Qin and Xie; preprint, 2026-07-27 | Its 427 samples cover source-to-test, comment-to-context, trace-to-code, edit-to-ripple, and no-local-answer situations. Ranking, recall, and budgeted-context metrics select different winners. | Repository navigation extends beyond semantic similarity and imports. Uneven repository representation and file-level labels limit conclusions; retrieval scores do not establish end-to-end repair success. |
| R12 | [SWE-CI](https://arxiv.org/html/2603.03823v4), Chen et al.; preprint, 2026-04-01 | Evaluates 100 evolution tasks from 68 repositories through repeated architect/programmer iterations. Base-to-target histories average 233 days and 71 commits; evolving test outcomes provide a maintainability proxy. | Supplies a way to observe consequences across changes. Target-test-driven generated requirements, Python selection, and stable-dependency spans differ from unrestricted product evolution. The proxy does not capture all maintainability. |
| R13 | [SlopCodeBench](https://arxiv.org/html/2603.24755v2), Orlanski et al.; preprint, 2026-05-07 | Across 36 problems and 196 checkpoints, structural erosion increased in 77% of evaluated trajectories and verbosity in 75.5%. Quality guidance improved initial metrics without arresting degradation. | Architectural freedom and repeated extensions reveal failures hidden by one-shot evaluation. Curated difficulty and author-defined structural metrics matter; comparisons with human repositories are not randomized or task-matched. |
| R14 | [The Devil Is in the Interface](https://arxiv.org/html/2608.11386v1), Xu et al.; preprint, 2026-08-11 | Six tool interfaces, three models, and 11,700 main trajectories show changes in consistency, exploration, and cost. The authors report 56.3% lower token usage for Python code-action interfaces versus BashOnly, with similar task performance; the detailed cost discussion emphasizes cumulative input tokens. | A strong reason to control the harness in architecture trials. The main experiment has 65 tasks and prototype interfaces; token savings here cannot be attributed to repository design. |
| R15 | [Mining Architectural Quality Under Agentic AI Adoption](https://arxiv.org/html/2606.13298v1), Larsen and Moghaddam; author manuscript, 2026-06-11; arXiv record reports SEAA 2026 acceptance | A difference-in-differences study of 151 Java repositories reports essentially unchanged smell counts (+1.1%, p=.82), growing code volume (+12.8%, p=.003), and lower smell density. | The density decline is primarily a denominator effect. Adoption is detected through configuration/commit proxies; identification assumptions, analysis attrition, and a limited follow-up constrain causal interpretation. This is no evidence of universal architectural improvement or deterioration. |

## 3. What the evidence changes about AGENT

### Optimize a complete change episode

The relevant outcome is an accepted change, including discovery, implementation, regression verification, and handoff. A lower token bill obtained by skipping necessary checks is not an improvement. A shorter patch that postpones an inevitable migration can make the next change harder. Treat acceptance rate and total cost as separate outcomes and compare their tradeoff under equivalent constraints.

This framing is an engineering proposal informed by the evidence, rather than a result reported by one paper. It moves the concept from preferences about how code looks to questions an experiment can answer. “Can the agent independently modify this behavior?” and “What must it inspect or execute first?” are more actionable than whether a repository appears agent-friendly.

### Replace atomicity with addressability

The original **Atomic Context** name suggests a naturally complete small unit. Real changes may require an interface, a schema, a deployment binding, a downstream consumer, and several tests. **Addressable Context** instead requires a reliable route to the appropriate authorities, with expansion when the initial scope proves incomplete.

Long-context limitations [R5](https://arxiv.org/html/2502.05167v3) coexist with effective external navigation [R7](https://arxiv.org/html/2603.20432v1). The hypothesis should therefore concern the cost of acquiring sufficient evidence. It should not require the entire system to fit into one prompt. Tiny files, huge files, terse identifiers, and expansive prose can all obstruct that acquisition in different ways.

### Make relationships queryable

The useful graph includes implementation selection, configuration, effects, schemas, callers, and tests. A dependency diagram that omits runtime wiring can be accurate about imports and misleading about behavior. Prefer generated or validated relationships over a second manually maintained description of the system.

Graph retrieval's mixed neighborhood-size results [R4](https://arxiv.org/html/2410.14684v2) motivate selective traversal. The diverse retrieval tasks in [R11](https://arxiv.org/html/2607.24882v1) motivate broader relation types. Neither result proves that a particular graph schema improves architectural quality. Unknown dynamic edges must remain visible, with broader verification when needed.

### Judge abstractions by their lifecycle economics

An abstraction can reduce repeated reasoning by exposing a stable contract. It can also require discovering a factory, registry, adapter, configuration layer, and hidden mutable state before a local change is safe. Both outcomes are plausible; counting interfaces cannot distinguish them.

**Economic Abstraction** proposes comparing total verified-change cost over representative future tasks. Include the cost of testing, retrieving, documenting, and maintaining the abstraction. Familiar conventions can be valuable because agents already know how to navigate them. The reviewed evidence supplies no basis for categorically replacing OOP, dependency injection, frameworks, or information hiding.

### Measure semantic change scope

**Narrow Change Surface** concerns decisions and effects, not raw diff size. One-file changes can affect every customer; a broad mechanical migration can be appropriately bounded. An expected impact scope is a prediction to check, not a restriction that excuses missed consumers.

Separate changed owners, affected contracts, generated artifacts, and operational migrations. Track both local and cross-cutting tasks. The metric lesson in [R15](https://arxiv.org/html/2606.13298v1) generalizes cautiously: always expose the numerator and denominator behind an appealing ratio. More code can improve a density score without removing a defect.

### Extend executable rules into traceable verification

**Traceable Verification** extends the original Testable Architecture idea: connect the task, changed artifacts, affected contracts and effects, executed checks, and resulting evidence at a specific revision. A check must reject a known violation for the intended reason. Evidence must become invalid when the checked artifact changes.

This is a proposed mechanism, not a demonstrated finding of the cited papers. Its purpose is to support agent-to-agent handoff without dependence on conversation memory. A verification receipt records observed results and limitations; it does not expose private reasoning or establish truth merely because it contains a hash. Acceptance requires authority independent of the implementation agent's ability to edit its own tests.

## 4. Counterevidence and alternative explanations

Documentation is not a free optimization. The latest instruction-file study reports nonsignificant success differences versus no context, greater cost, and limited navigational value from overviews. Its documentation-removal ablation also shows why “all context files are harmful” overstates the result. [R8](https://arxiv.org/html/2602.11988v3)

Longer-term configuration associations do not refute that experiment. The RAMP study measures different populations and quality proxies, with nonrandom maturity and possible reverse causality. Immediate issue resolution and sustained adherence to conventions are different outcomes. [R9](https://arxiv.org/html/2608.25241v2)

Likewise, architectural erosion is not established merely because agent-written methods are complex. The Java mining study distinguishes code-level and architectural measures and finds no significant total-smell increase in its observed period. Its result neither proves safety nor supports a general deterioration narrative. [R15](https://arxiv.org/html/2606.13298v1)

Any apparent AGENT benefit could come from better tests, stronger task descriptions, a newer model, or a different harness. Source organization is only one variable. Interface effects in [R2](https://arxiv.org/html/2405.15793v3) and [R14](https://arxiv.org/html/2608.11386v1) make this confounding especially important. A useful experiment must isolate the proposed intervention before crediting the mnemonic.

Finally, future models may navigate today's difficult structures cheaply. Additional manifests and indices can then become overhead. AGENT mechanisms should survive because they improve measured outcomes, not because agents are assumed permanently incapable of familiar engineering abstractions.

## 5. Falsifiable claims and evaluation priorities

The following are proposed hypotheses. Each needs a declared task population, model, harness, budget, acceptance mechanism, and repeated-run design. None is currently a demonstrated repository result.

| Hypothesis | Observable outcome | Evidence against it |
|---|---|---|
| Addressable task routes improve evidence acquisition. | Fewer tokens or steps to sufficient relevant evidence, preserving acceptance. | The route adds overhead, misses constraints, or gives no repeatable benefit. |
| Explicit, current relationships improve impact prediction. | Fewer missed consumers and undeclared effects under equivalent checks. | Graph upkeep exceeds savings, or dynamic gaps remain undetected. |
| A contract can lower abstraction costs. | Callers complete tasks with fewer internal inspections and lower lifecycle cost. | Callers repeatedly inspect internals; duplication, drift, or maintenance cost grows. |
| Cohesive ownership improves local change behavior. | Fewer unrelated synchronized edits without missed migrations or regressions. | Benefits vanish on held-out or cross-cutting tasks. |
| Revision-bound evidence improves independent handoff. | Fresh agents identify checked behavior and reject stale or weakened evidence. | Receipts become ceremonial, self-attested, or too expensive to maintain. |

The initial experiment should compare four conditions: original source with ordinary documentation; original source plus minimal agent guidance; behavior-preserving architectural changes with equivalent documentation information; and both interventions together. Hold the model, harness, tools, environment, task, oracle, and resource limits fixed. Randomize run order, repeat attempts, and report failures rather than selecting successful demonstrations.

Design refactors before revealing held-out future changes. Otherwise the experiment measures foreknowledge. Include sequential extension, fresh-agent handoff, cross-cutting migrations, and unfamiliar repositories across languages. Evolving-task work [R12](https://arxiv.org/html/2603.03823v4) and [R13](https://arxiv.org/html/2603.24755v2) supplies motivation for this temporal component; neither benchmark alone establishes the right test distribution for AGENT.

Report independently checked acceptance first, then total spending across assigned runs, retries, tools, indexing, checks, and metadata upkeep. Distinguish input, cached input, output, and observable reasoning tokens; report missing usage rather than inventing it. Context-window occupancy, unique evidence read, and cumulative processed tokens answer different questions.

Navigation diagnostics should include first relevant evidence, repeated retrieval, relevant-span yield, missed constraints, and predicted versus observed impact. File hits alone can hide substantial within-file work, as exploration research emphasizes. [R10](https://arxiv.org/html/2606.07297v1) Static metrics remain explanatory signals, not a substitute for task outcomes.

Publish preregistered success margins, uncertainty intervals, repository-level breakdowns, excluded cases, model and harness versions, environment manifests, patches, and sanitized traces. Report negative results and amortization assumptions. If a mechanism helps only one task family or agent, preserve that narrower claim. The [benchmark protocol](benchmarks/PROTOCOL.md) defines how this repository intends to collect such evidence; until then, AGENT remains a testable proposal.
