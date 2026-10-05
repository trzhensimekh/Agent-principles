# AGENT evaluation protocol

Status: proposed larger experiment. A separate [exploratory source-code study](../experiments/README.md) records a small set of actual agent outcomes; it does not execute this full protocol. Structural checks and illustrative examples establish that rules can be enforced; they do not establish that agents become faster, cheaper, or more reliable.

## 1. Claim and unit of evidence

The primary source-design claim is: for a specified distribution of implementation and maintenance tasks, agent models, and execution budgets, AGENT coding guidance produces code that agents can implement and subsequently change with greater verified success or lower total cost at comparable success. Benefits must survive competent baseline guidance, equivalent task information, equal tooling, and independent hidden evaluation. A complementary structural experiment compares behavior-equivalent architecture variants to investigate the mechanism separately from the prompting intervention. The proposed mediator is [agent legibility](../docs/LEGIBILITY.md), which needs direct diagnostic measurements as well as task outcomes.

The principal experimental unit is a repository with a distribution of tasks. Repeated model runs are observations within tasks, and tasks are clustered within repositories. Hundreds of attempts on one repository do not establish generality across repositories. Architecture variants are treatments, not different products. Do not describe lower token consumption alone as improved engineering.

Both tracks address autonomous implementation and maintenance. It does not establish human productivity, product value, universal superiority over object orientation, or transfer to every language and framework.

## 2. Register the experiment before running it

Publish a timestamped protocol and hashes of the run manifest, task inventory, variants, evaluator, and analysis code. Keep task solutions and hidden checks private until completion. Specify model/version, provider, reasoning configuration, agent scaffold, context and output limits, retry policy, allowed tools, dependency cache policy, platform, task selection rule, time budget, cost budget, statistical estimands, and exclusion rules.

Register one primary hypothesis and a smallest useful effect. An example decision rule is a reduction of at least 15% in total provider cost per verified success, with success-rate noninferiority margin of 5 percentage points. These numbers are proposed engineering preferences, not research-established constants. If correctness improvement is the objective instead, preregister that as primary. Do not swap primary outcomes after observing results. Determine confirmatory sample size from pilot variability and repository clustering; the pilot itself cannot justify a population-wide claim.

Freeze source snapshots and keep all failures in the denominator. Infrastructure failures may be rerun only under a predefined rule applied equally to all arms. Report original and rerun records. Never remove a task because an agent discovered an inconvenient defect.

## 3. Baselines and interventions

### Track A: coding guidance, then unseen maintenance

Give fresh builder agents the same initial behavioral requirements and ordinary working tools. Compare ordinary engineering instructions, equally concise established-design guidance (such as contracts and SOLID where applicable), and AGENT. A separate comparison with Context Minimization Principle guidance can test whether AGENT adds value beyond its closest prior art. Freeze and publish every guidance document; avoid a weak or deliberately verbose comparator. Record the added instruction cost.

Let each builder choose its implementation. Evaluate generated code with the same independent acceptance suite, then give fresh agents previously withheld change sequences. Keep maintainer instructions neutral to study the effect of generated structure. A separate factorial can apply guidance to maintenance too, but that answers a different question and must be declared in advance. Do not reveal future changes while choosing the initial architecture.

Preserve unsuccessful generations and follow-ups under a registered policy; do not select only easy-to-maintain successes. The dependent generation/maintenance chain is the observation within each task family and repository specification. Repeat generations, randomize assignment/order, and cluster analysis accordingly. Inspect whether the source structures actually differ; a guidance comparison that produces the same designs may be non-discriminating.

This is the main evaluation path for AGENT as coding principles. The completed [small study](../experiments/README.md) used a limited version with two conditions, two domains, and one follow-up. It did not execute the full controls, repetitions, or telemetry proposed here.

### Track B: behavior-equivalent structural variants

This complementary track tests particular source-design choices while separating documentation and harness changes. It evaluates a mechanism; it is not a requirement to build repository-optimization tooling.

Use existing, competent software as the baseline: maintained tests, ordinary modularity, established language conventions, and working developer commands. A deliberately tangled baseline answers a trivial question. Include both a strong conventional refactoring baseline and the AGENT candidate where feasible, so ordinary cleanup is not credited to the acronym.

Create paired variants that implement the same public behavior and start with equivalent defects. Before exposing them to agents, validate equivalent API responses, persisted state transitions, errors, authorization decisions, and relevant performance constraints with a common external oracle. Differential and property checks can supply evidence of equivalence, not proof for an arbitrary program. Document every intentional difference. Preserve dependencies and framework versions unless the specific experiment concerns them.

A full design crosses three binary factors:

| Factor | Control | Treatment |
| --- | --- | --- |
| Architecture | Competent conventional structure | Preregistered AGENT structural transformations |
| Documentation | Equal baseline instructions | Generated dependency maps, localized contracts, evidence index |
| Harness | Fixed shell/search/edit/test tools | Repository-specific navigation and verification interfaces |

Eight cells distinguish architecture effects from tooling and documentation effects and reveal interactions. Keep factual task knowledge equal between cells: treatment docs may reorganize or generate existing facts, but must not reveal hidden requirements. Equal information does not require padding both arms to the same token count; record document size and investigate it as a mechanism. Architecture-specific commands are part of the harness treatment, unless an explicitly declared architecture rule makes them inseparable. State that limitation rather than claiming a clean causal decomposition.

A feasible first pilot fixes the harness and uses four architecture/documentation cells: conventional source with baseline docs, conventional source with agent guidance, AGENT structure with baseline-equivalent docs, and AGENT structure with agent guidance. It cannot establish harness effects. Subsequent ablations change one principle at a time. Combined-package success does not show that every letter helps. Include null transformations such as harmless file rearrangement, and negative controls such as irrelevant metadata, to detect scaffold sensitivity and superficial benchmark adaptation.

## 4. Task construction and leakage

Select tasks before transformations are optimized. Mix bug fixes, behavior extensions, schema changes, external integration changes, dependency migrations, and diagnosis of a failing end-to-end flow. Include changes that should stay local and changes that legitimately cross boundaries. Include tasks that require revisiting earlier assumptions; AGENT must not win merely by simplifying the task distribution.

For each task define requirements independently of the candidate architecture, acceptance tests, regression tests, and a mapping between semantically equivalent locations across variants. A task adapter may translate paths and commands, but cannot supply the implementation. Use the same semantic bug or missing capability in each variant, not necessarily the same text patch. Hold out some repositories and task families entirely during design.

Public coding benchmarks are useful calibration, but repositories, issue texts, solutions, and tests may have entered model training or scaffold tuning. Newly authored private tasks reduce some leakage but cannot prove absence of training overlap. Record task provenance and creation dates. Avoid pretending a model's training cutoff is known. Keep hidden checks outside the agent workspace, disable undeclared network access, and prevent access to evaluator logs until the attempt is finished. Public development tasks and private evaluation tasks should be separate.

## 5. Execution and correctness

Run each task/model/variant/repeat combination in a clean, isolated checkout and fresh agent session. Randomize arm order within task/model blocks; balance provider-time windows to limit service drift. Reuse environment images, not cross-arm conversational memory. Use reproducible seeds where supported, while recognizing that seeds rarely guarantee deterministic hosted inference. Pin model snapshots when available and record provider changes when not.

Use one fixed autonomous attempt budget. Retries are attempts, not invisible free improvements. If best-of-N selection is used, charge all N attempts and define the selection process before the run. Manual intervention is disallowed for the primary autonomous outcome and recorded separately as escalation.

Evaluate the final patch with agent-visible checks and an independent hidden suite containing task acceptance and regression checks. Success requires both, as well as absence of prohibited behavior such as disabling tests or changing the evaluator. Public test edits may be legitimate, but hidden grading must not trust them. Record build failures, timeouts, budget exhaustion, invalid patches, regressions, and harness failures as separate failure reasons.

Strengthen the oracle using seeded faults, metamorphic checks, and mutation testing. A hidden suite that accepts a no-op or known-bad patch is not ready. Mutations should represent meaningful requirements, not only syntax trivia. Report which fault classes the oracle detects. Review successful patches for undeclared scope changes with a fixed rubric; an independent agent reviewer is a secondary signal, not a substitute for executable evidence. Disagreements should be resolved without access to treatment labels where practical.

## 6. Outcomes and instrumentation

The primary correctness measure is verified task success at the fixed budget. Report acceptance and regression outcomes separately as well as their conjunction.

Record complete resource accounting for every attempt, including failures: uncached input tokens, cached input tokens, output tokens, reasoning tokens where exposed, all tool calls and tool costs, retrieval/index construction, execution time, wall-clock time, retries, and infrastructure costs. Publish provider prices and date separately from raw counts. Token totals are not comparable across different tokenizers without qualification. Do not count cache hits as free unless the provider does. Track whether warm caches are shared between arms. Prefer balanced cold-start and warm-start analyses.

The total cost per verified success is total cost of all attempts divided by total verified successes. If there are no successes it is undefined, not zero. Also report total spend, success count, per-task cost, and cost among successes, clearly labeling the last measure as susceptible to survivor bias. Architecture can appear cheap simply because agents give up early; cost must always be read beside success.

Navigation measures include tool calls before the first relevant symbol, unique source bytes or tokens inspected, repeated reads, retrieval precision against a reviewer-defined relevance set, and time to first justified edit. These are process proxies; relevance sets can be incomplete and a broad read can prevent a regression.

Change-surface measures include changed semantic modules, files, dependencies, public interfaces, and unrelated diff content. Normalize or stratify by task family and variant's module granularity. A one-file monolith is not automatically better than five well-scoped modules. Check duplication, runtime overhead, and maintainability constraints to prevent gaming locality through copying or deleting functionality.

For end-to-end traceability, require a structured final evidence record linking requirement → entry point → implementation → relevant checks → observed result. Grade a sampled set against actual execution and dependency evidence. Report missing and false links separately. A fluent narrative or a large trace file is not evidence. Charge trace-generation cost.

## 7. Analysis and stopping

First show per-repository and per-model results, paired task outcomes, and all failure categories. Estimate paired success differences and paired cost differences within task/model blocks. Repeats improve estimates of stochastic behavior; they must not be treated as new independent tasks or repositories.

For confirmatory intervals, resample repositories and then tasks within repositories, preserving paired arms and repeated observations; or use a preregistered hierarchical model with repository/task effects and model interactions. Report 95% intervals, not only point estimates. With very few repositories, cluster uncertainty is poorly identified: show raw paired results and label inference exploratory. The included analyzer intentionally supplies descriptive aggregates only and makes no confidence or significance claims.

A cost-per-success ratio can be unstable with few successes. Report its components and bootstrap sensitivity; do not discard resamples with zero successes without disclosure. Define noninferiority using the interval for the success difference. A nonsignificant difference does not establish equivalence. Test model-specific effects explicitly and avoid extrapolating two tested models to all future agents. Correct or hierarchically structure multiple secondary comparisons; diagnostic plots can remain exploratory if labeled.

Stop only at the registered sample or a registered sequential boundary. Budget exhaustion is a legitimate stop reason but must not be presented as a successful confirmatory study. Publish negative and mixed findings, including which principles failed and which tasks became worse.

## 8. Example structural pilot and longitudinal follow-up

For Track B, start with three repositories spanning at least two languages, six held-out tasks per repository, two independently developed agent models, four architecture/documentation arms, and two repetitions: 288 runs. Analyze each preregistered paired contrast separately; the included analyzer handles two-arm contrasts. This is a feasibility pilot, not a sample-size guarantee. With an illustrative cap of $2 per run, model spend is at most $576 before infrastructure, task construction, and indexing; actual budgets should be set from one dry run without using its task in evaluation. A smaller smoke test may validate instrumentation only. Do not report it as agent efficacy.

After the pilot, estimate variance and failure rate, fix instrumentation bugs without changing hypotheses silently, and size a new confirmatory study on fresh tasks. Run the factorial extensions only if the pilot can reliably execute and grade tasks.

Agent-maintained architecture also needs longitudinal evidence. Run a preregistered sequence of 10–20 dependent changes per repository, preserving history within each arm. Measure cumulative spend, retained correctness, dependency cycles, stale context artifacts, repair overhead, and ability of a fresh agent to resume after a handoff. Include an agent that proposes architecture changes under fixed constraints; independently grade its results. Single-issue success cannot establish that a design remains navigable after months of autonomous maintenance. Report the one-time migration and artifact-maintenance costs and estimate the number of successful changes required to repay them.

## 9. Publication and evidence ladder

Publish runnable variants, immutable run manifests, container recipes, task provenance, evaluator hashes, machine-readable results, analysis code, redacted tool traces, and limitations. Release hidden tests after the experiment or provide an independent evaluation channel when reuse requires secrecy. Do not expose credentials or private repository content.

Use explicit evidence levels: **proposed** (argument), **executable** (rules and examples run), **pilot-tested** (limited agent experiment), **replicated** (independent held-out confirmation). AGENT remains an experimental set of source-code principles with executable demonstrations and a small exploratory agent study. No general efficiency percentage is claimed.

## Methodological sources

These sources motivate experimental choices; they do not validate AGENT. See [RESEARCH.md](../RESEARCH.md) for inspected source versions, results, and limitations.

- [SWE-bench](https://arxiv.org/html/2310.06770v3) and its [evaluation harness](https://github.com/SWE-bench/SWE-bench): repository-level issue resolution and executable grading.
- OpenAI, [Why we no longer evaluate SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) (2026-02-23): benchmark validity and contamination require explicit examination. Its reported audit concerns 138 selected difficult cases, not an unbiased estimate over every benchmark instance. Do not reuse a famous benchmark as an unquestioned oracle.
- [Evaluating AGENTS.md](https://arxiv.org/html/2602.11988v3): motivates documentation controls and cost accounting rather than assuming more instructions help.
- [The Devil Is in the Interface](https://arxiv.org/html/2608.11386v1): motivates fixing or crossing the agent harness as a separate experimental factor.
- [SWE-Explore](https://arxiv.org/html/2606.07297v1): budgeted evidence acquisition measures and the limits of relevant-region labels.
- [SWE-CI](https://arxiv.org/html/2603.03823v4) and [SlopCodeBench](https://arxiv.org/html/2603.24755v2): motivate evaluating sequences of changes rather than only isolated patches.
