# Adopting AGENT with autonomous maintainers

Start with one recurring maintenance task. The unit of adoption is a verified change path, not an entire repository rewrite.

## 1. Establish the existing outcome

Pin a repository revision, model version, harness, environment, and a task with externally stated acceptance criteria. Save the agent's observable actions, usage, patch, test results, and failures. Do not infer unseen reasoning or missing token usage.

Preserve the existing behavior and verification suite while comparing structures. If the original suite is inadequate, improve it identically for both variants before attributing a benefit to architecture.

## 2. Find the actual context failure

Classify the failure before adding structure:

| Observed failure | Candidate intervention | Necessary check |
|---|---|---|
| Agent cannot locate the owner. | Stable task/symbol entry point. | Fresh-context locate-and-change trial. |
| Agent finds code but misses a rule. | Put an executable contract beside its authority. | Boundary or property test plus a negative control. |
| Agent misses a runtime binding. | Expose the composition/configuration route. | Binding and effect assertion. |
| Agent repeats broad searches. | Small task view derived from source references. | Context-view ablation; include maintenance cost. |
| One decision requires scattered edits. | Consolidate its ownership or expose the shared contract. | Sequential changes and downstream tests. |
| A passing patch uses weakened tests. | Isolate the acceptance oracle. | Attempted oracle-edit rejection. |

Model inability, ambiguous requirements, flaky environments, and broken tools are different failure classes. Architecture cannot fix all of them.

## 3. Make the smallest useful structural change

Keep one authority for each fact. Generate projections from code, schemas, or build metadata where possible. Use stable symbols rather than line numbers for maintained references. Keep task context selective and resolve it on demand.

Do not create a new interface for every function, a manifest for every file, or a permanent agent role for every module. Each mechanism adds retrieval, execution, and upkeep costs. Delete mechanisms that fail their ablation.

## 4. Give the agent a verifiable handoff

An agent beginning a task should be able to answer, through repository artifacts:

```text
What must become true?
What must remain true?
Where is the responsible decision?
Which consumers, data, and effects can be affected?
What evidence will distinguish a correct change?
Which facts are still unresolved?
```

The exiting agent leaves the patch, concise decision/impact record, check results, and artifact identities. A subsequent agent should not need the predecessor's conversation to verify the work.

## 5. Handle real end-to-end changes

For database, network, or asynchronous behavior, code-level tests alone are insufficient. Include the relevant subset of:

- schema compatibility and data migration;
- transaction boundaries, idempotency, retries, and ordering;
- producer/consumer contracts and configuration-selected behavior;
- deployment compatibility, observability, rollback, and recovery;
- permission and resource constraints at the actual effect boundary.

Record untested production effects explicitly. The reference refund example stops at a local database transaction and an outbox record; it does not demonstrate settlement at a payment provider.

## 6. Coordinate multiple agents

Assign tasks around decision ownership and contract boundaries. A textual merge is not evidence of semantic compatibility. Record base revisions and expected read/write boundaries; after integration, rerun checks against the combined candidate. Regenerate receipts for that candidate.

Shared mutable registries and duplicated policy facts can become coordination bottlenecks. Measure conflicts, repair attempts, and duplicated context acquisition before adopting parallelism as an optimization.

## 7. Keep verification independent

An agent-only maintenance system can use an isolated evaluator with fixed acceptance fixtures and a protected promotion mechanism. Proposed changes to those controls need a separate validation route. This is separation of authority, not a requirement that every change wait for a human.

The local demo deliberately does not implement this security boundary. Its scripts are editable by the same process that edits the application. Use its receipts as reproducibility records, not authorization to deploy.

## 8. Decide using evidence

Run the [benchmark protocol](../benchmarks/PROTOCOL.md) against baseline and intervention variants. Keep improvements that survive correctness checks, cost accounting, and repeated changes. Retain negative results: they identify where a structural idea fails.
