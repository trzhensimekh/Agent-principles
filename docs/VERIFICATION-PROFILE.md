> Supporting material from v0.2. The current core is the [source-code design principles](../SPECIFICATION.md). This profile is optional and does not define AGENT.

# AGENT v0.2 — The agent change contract

Status: experimental specification · Evidence reviewed: 2026-10-05

AGENT specifies properties of software maintained by coding agents. Its unit of analysis is a **verified change**, including discovery, implementation, regression checking, and evidence handoff. It applies to ordinary software; that software does not itself have to contain an LLM.

The intended maintainer can be an autonomous agent with no conversation history and no access to the original author. The architecture must expose the information and feedback necessary for that agent to work. Agent-only maintenance still requires externally supplied objectives and a verification authority: an agent cannot establish that its own interpretation is the intended behavior merely by generating matching tests.

## 1. Scope and terminology

**Task**: a requested change with observable acceptance criteria and preserved constraints.

**Task context**: the artifacts an agent uses to perform a task: code, contracts, schemas, configuration, fixtures, relevant decisions, and tool feedback. A context manifest describes a candidate context, not a proof that nothing else matters.

**Owner**: a code boundary responsible for a decision or invariant. Ownership is a structural fact; it need not refer to a person.

**Effect**: an externally observable operation, such as a persisted write, network request, emitted event, permission decision, or filesystem change. Imports alone do not describe effects.

**Change surface**: the implementation, contracts, data, configuration, and deployment artifacts that must change together for a task. Count generated artifacts separately, but do not hide their operational cost.

**Oracle**: an acceptance mechanism that distinguishes acceptable from unacceptable outcomes within a stated scope. Examples include an independently specified contract suite, a schema compatibility check, or a property with a sound proof. An LLM's approval is a fallible signal, not an oracle of correctness.

**Verification receipt**: a machine-readable record binding executed checks and their outcomes to the artifacts and environment that were checked. A hash establishes identity; it does not make a check correct or a receipt authentic.

**Unknown edge**: a dependency or effect that available analysis cannot resolve. Unknown must remain an explicit result rather than being silently treated as absent.

MUST and SHOULD below define this experimental profile. They do not claim universal software-design laws or an external standards body's endorsement.

## 2. Optimization target

For a repository design `D`, task distribution `T`, agent/model `M`, harness `H`, and resource budget `B`, measure:

```text
P(accepted change | D, T, M, H, B)

aggregate cost per accepted change =
    cost of all assigned runs, including failed runs and retries
    / number of accepted changes
```

If no change is accepted, the second quantity is undefined; report failures and total cost. It is not zero.

For repeated trials, the denominator counts accepted run episodes, not unique tasks. Report unique-task coverage separately and keep failed attempts within their assigned episode. Publish both per-repository results and the chosen aggregate weighting so a large easy repository cannot silently dominate the result.

Acceptance includes the requested behavior, preserved regressions, relevant boundary/effect constraints, and the declared evidence requirements. Choose task-specific performance and reliability constraints before the experiment. Report correctness and cost separately; use a Pareto comparison instead of inventing one universal architecture score.

An independently controlled **acceptance profile** MUST define required claims, the execution/deployment scope, allowed residual unknowns, and conditions that block promotion before evaluating a candidate. A required claim that fails, remains unverified, or has stale evidence blocks acceptance. An implementation agent cannot convert that claim into a reported limitation to pass. Repository-only acceptance does not imply deployment acceptance: migrations, rollout, and recovery enter the profile when the task affects them.

Cost includes model usage, tool execution, retrieval/indexing, verification, and amortized maintenance of additional artifacts. Record input, output, cached, and reasoning tokens separately when observable. Bytes, lines, file counts, and estimated tokens are different measurements. Missing provider usage must be reported as missing.

AGENT's hypothesis is that the following properties can improve this frontier on some realistic task distributions. **This repository has not yet demonstrated that hypothesis in a controlled agent trial.**

## 3. The five principles

| Principle | Required outcome | Typical mechanism | Falsifying observation |
|---|---|---|---|
| **A — Addressable Context** | An unfamiliar agent can locate task-relevant authorities and resolve their versions. | Stable symbols, task entry points, small validated context views. | Needed constraints repeatedly remain undiscovered; the index costs more than it saves. |
| **G — Graph Explicitness** | Relevant dependency, data, configuration, and effect paths can be followed. | Explicit composition, schema references, declared unresolved edges. | A supposedly bounded change breaks an undisclosed consumer or effect. |
| **E — Economic Abstraction** | A contract reduces total change cost while preserving correctness. | Stable interfaces, direct implementations where useful, measured ablations. | Users must inspect internals anyway, or lifecycle cost rises without an acceptance benefit. |
| **N — Narrow Change Surface** | A decision has an identifiable owner; necessary changes remain bounded by actual coupling. | Cohesive policy ownership, compatibility boundaries, separate generated artifacts. | Routine tasks require synchronized edits across unrelated owners or omit required migrations. |
| **T — Traceable Verification** | Evidence connects the task and changed artifacts to relevant checks at the tested revision. | Contract tests, architecture checks, effect assertions, version-bound receipts. | A known violation passes, evidence is stale, or the implementer can silently weaken the acceptance gate. |

### A — Addressable Context

**Rule:** For a declared task family, the repository MUST provide a discoverable route to the owning implementation, relevant contracts, and verification commands. Machine references MUST resolve or fail explicitly.

The route may be ordinary language tooling, a module interface, a build graph, an existing schema registry, or a generated task view. A new manifest is optional. Duplicating information already cheaply discoverable is a cost that needs justification.

The selected view SHOULD contain:

- the decision being changed and the authoritative code or specification;
- entry points, relevant inputs, units, states, and boundary conditions;
- required preserved properties and their checks;
- cross-boundary dependencies, effects, and unresolved questions;
- the revision or content identity of referenced artifacts.

**Check:** Resolve references and run a fresh-context maintenance task. Record navigation effort, missed constraints, repeated retrieval, and task success. Remove or vary the context view to test whether it helps.

**Negative control:** Delete or rename a referenced symbol without updating its locator. The reference validator must fail. This verifies addressability, not semantic sufficiency.

**Tradeoff:** A short context can omit critical facts. A large context can bury them. There is no universal maximum file size or token count. A bounded context is task-relative and can expand when the initial boundary is wrong.

### G — Graph Explicitness

**Rule:** For important task paths, the repository MUST expose how declared interfaces connect to implementations and effects. Analysis MUST distinguish known edges from unresolved dynamic behavior.

Relevant graph relations include:

```text
task -> changes -> decision owner
entry point -> calls -> implementation
implementation -> reads/writes -> schema or state
configuration -> selects -> implementation
implementation -> emits/consumes -> event
effect -> observed by -> check or runtime signal
invariant -> enforced by -> check
```

A graph does not require a graph database. Imports, typed contracts, build metadata, explicit composition, manifests, and runtime traces can supply different parts of it. Prefer deriving edges from authoritative artifacts over maintaining a duplicate hand-written map.

Evidence MUST distinguish declared, statically derived, and observed edges, with their source and revision. Unknown means unresolved under the stated analysis; it is different from an edge proven absent within a supported subset.

**Check:** Trace representative paths through their data and side effects; reconcile declared edges with static analysis and controlled runtime observations. Record analysis coverage, dynamic gaps, and observed undeclared effects. A successful trace covers that execution, not every possible execution.

**Negative control:** Add a forbidden dependency or a known undeclared effect. The corresponding check must fail. Import checks do not substitute for effect checks.

**Tradeoff:** Complete static dependency discovery is generally unavailable in dynamic systems. For an unresolved edge, broaden verification, inspect the binding, or stop autonomous promotion for that scope. Do not infer safety from the absence of a discovered edge.

### E — Economic Abstraction

**Rule:** An abstraction SHOULD permit callers to reason from its contract for common tasks. Retain, add, split, or remove it according to measured change cost and correctness, including its verification and metadata costs.

The relevant comparison is between feasible designs under equivalent tasks. Fewer classes, fewer interfaces, or less code is not the objective. A dependency-injection container may be useful if its bindings are cheaply inspectable; a direct function may be cheaper when variation is unnecessary.

**Check:** Compare task outcomes with and without the abstraction. Record how often callers inspect internals, the context retrieved, repair attempts, verification cost, and maintenance of the abstraction itself.

**Negative control:** Hide an unstable or underspecified behavior behind an interface. If callers cannot complete representative tasks from the contract, that abstraction has not established a useful reasoning boundary.

**Tradeoff:** Duplication can reduce immediate navigation while increasing future drift. Centralization can narrow policy changes while creating a dependency bottleneck. Measure a sequence of changes, not only the first edit.

### N — Narrow Change Surface

**Rule:** A business or technical decision SHOULD have a clear owner. Before a change, the agent SHOULD identify an expected impact scope; after the change, it MUST account for material edits and required effects outside that scope.

The expected scope is a prediction, not a permission to omit work. A schema migration, consumer update, compatibility shim, deployment setting, and rollback plan may all be necessary for a small code edit.

**Check:** Compare expected and actual changed owners and contract dependents. Check behavior at downstream boundaries. For parallel agents, track overlapping writes and read/write assumption conflicts even when text merges cleanly.

**Negative control:** Duplicate a policy in a consumer and change only the declared owner. A cross-boundary behavioral test must expose the inconsistency.

**Tradeoff:** Do not optimize raw file count. Splitting or merging files can game that number without improving change locality. Cross-cutting tasks are a required test stratum, not outliers to exclude.

### T — Traceable Verification

**Rule:** Each important acceptance claim MUST identify an executable check or explicitly state that it is unverified. Evidence MUST identify the tested inputs, the check definitions, the observed results, and the execution scope.

The minimum trace is:

```text
requested behavior
    -> decision and declared impact
    -> changed artifacts
    -> affected effects/contracts
    -> executable checks
    -> results bound to artifact identity
```

A receipt SHOULD include task ID, base revision, candidate content digest, check-set digest, tool/runtime versions, commands and exit status, evidence artifact digests, and unresolved limitations. Record dirty working-tree state; a Git commit identifier alone does not identify uncommitted inputs.

**Check:** Deliberately violate an important rule and verify rejection for the intended reason. Change a source or check after generating a receipt and verify that the old receipt is rejected for the new candidate.

**Authority separation:** An implementation agent can propose tests and verifier changes. A promotion gate MUST evaluate them through an independently controlled acceptance path. The same agent must not obtain acceptance merely by editing the assertion, manifest, or workflow that rejects its patch. Independent authority can be an isolated automated evaluator; it does not require a human reviewer on every change.

**Tradeoff:** Tests establish their encoded properties for the exercised scope. Mutation checks demonstrate selected detector sensitivity. Hashes identify bytes. None proves complete requirements, production safety, or general architectural quality.

## 4. An agent's change loop

1. **Locate:** identify the task, its acceptance criteria, decision owner, and candidate context.
2. **Resolve:** follow relevant code, data, configuration, and effect edges; record unknowns.
3. **Predict:** declare expected impact, preserved constraints, verification plan, and material alternatives.
4. **Change:** implement within that scope; revise the prediction when evidence expands it.
5. **Verify:** execute behavioral, boundary, effect, and relevant regression checks at the candidate revision.
6. **Challenge:** test selected negative controls and check for weakened or stale acceptance mechanisms.
7. **Record:** emit evidence and unresolved limitations; independently gate promotion.
8. **Learn:** compare predicted and actual navigation/change cost. Remove ineffective metadata and fix recurring undiscoverable dependencies.

Persist concise decisions and evidence, not private chain-of-thought or full conversation transcripts. A useful record says what changed, which constraints mattered, what evidence supports it, and what remains unknown.

## 5. Conformance and evidence levels

Avoid a single "AGENT-compliant" badge. State exactly what has been demonstrated:

| Level | Meaning | What it does not establish |
|---|---|---|
| Declared | Task routes, owners, effects, and acceptance claims are documented. | That declarations match code. |
| Structurally checked | Specified references/boundaries resolve and pass executable checks. | Semantic completeness or agent usability. |
| Behaviorally checked | Declared scenarios and negative controls pass against identified inputs. | Better agent performance or production coverage. |
| Experimentally evaluated | Controlled agent trials report correctness and full costs against baselines. | Transfer to every model, harness, repository, or future task. |

The reference example targets the middle two levels for a deliberately small scope. It is not a general conformance certifier or an independently secured promotion service.

## 6. Failure conditions for the proposal

Revise or reject a mechanism when controlled trials show:

- context views add cost without improving acceptance or navigation;
- graph upkeep and staleness outweigh discovery savings;
- apparent local improvements disappear on cross-cutting or sequential tasks;
- the benefit comes entirely from the harness or tests, with no architecture effect;
- better agents remove the benefit, leaving only maintenance overhead;
- optimization lowers token use while increasing missed regressions or operational failures.

These outcomes are valid results. The mnemonic must not be protected from evidence.

## 7. Relationship to v0.1

The first proposal used **Atomic Context** and **Testable Architecture**. v0.2 uses **Addressable Context** to avoid implying one naturally complete atomic unit, and **Traceable Verification** to include the end-to-end evidence requirement. Graph Explicitness, Economic Abstraction, and Narrow Change Surface remain, with sharper checks and limitations.

AGENT builds on information hiding, contracts, dependency management, architectural fitness functions, Context Architecture, and the Context Minimization Principle. Its contribution here is an operational profile, a small executable example, and a falsifiable evaluation program. See [research](../RESEARCH.md) and [prior art](../docs/PRIOR-ART.md).
