# Executable AGENT reference: a refund-request ledger

This small Python system gives an agent explicit starting points, a declared dependency graph, bounded policy ownership, and executable checks. It accepts an eligible full-refund request and persists that request together with an outbox event in one SQLite transaction. It is an executable illustration, not evidence that this architecture improves agent performance.

**Scope:** immutable paid-order records; one full refund request per order; idempotent retries; an eligibility window of 30 elapsed 24-hour days measured using UTC instants. A refund *request* does not mean a payment was settled. No payment provider, dispatcher, authentication layer, partial refunds, schema migration system, or production deployment is included.

Python **3.11+** is sufficient. There are no third-party dependencies. Run these commands from `examples/reference`:

```sh
python demo.py
python tools/context.py refund-window
python -m unittest discover -s tests -v
python tools/negative_controls.py
python verify.py --receipt /tmp/agent-reference-receipt.json
python verify.py --check-receipt /tmp/agent-reference-receipt.json
```

The demo uses and removes a temporary database. The verifier prints JSON and returns a nonzero exit code on failed checks or observed input changes. Write its receipt outside this example directory, which is the measured input scope.

## Navigate a task

Start with [contract.json](contract.json), or ask `tools/context.py` for a task. The output identifies the entry point, authoritative policy owner, relevant files, allowed change scope, invariant checks, effect implementations, and composition binding. It reports file line counts, which are neither token measurements nor an assertion that the declared context is sufficient for every change.

| Task | Owner | Expected implementation changes | Required evidence |
|---|---|---|---|
| `refund-window` | `refunds/domain.py:approve` | The policy module; associated tests and claim text | Exact time boundaries, state rules, rejection effects, retry semantics |
| `storage-adapter` | `refunds/sqlite_ledger.py:SQLiteLedger` | Adapter and composition; associated tests and graph | Durability, atomicity, idempotency, uniqueness, permitted dependencies |

The manifest's `change_scope` is a review expectation, not a file-count quota or a permission system. A task that changes a contract can legitimately expand its scope; the agent should explain and update the affected contract rather than hide the expansion. Claims contain readable semantics; the named tests are a finite selection of counterexamples to incorrect implementations.

## Follow an operation

```text
demo.py / caller
  ├─ composition.open_ledger → SQLiteLedger
  └─ service.request_refund
       ├─ RefundLedger.get_request → existing-key replay or conflict
       ├─ RefundLedger.get_order
       ├─ domain.approve → pure time/state/amount policy
       └─ RefundLedger.record → SQLiteLedger.record
            └─ transaction: refund_requests row + refund.requested outbox row
```

`service.py` receives the ledger and time explicitly. `domain.py` depends only on `dataclasses` and `datetime`; the import checker rejects a direct SQLite dependency there. `ports.py` specifies the adapter's observable behavior. `composition.py` identifies the selected adapter. There is one adapter, one business operation, and one policy owner; there is no plugin registry or generic policy engine.

Retries return the original request, including its original timestamp, even after the eligibility window has expired. The database rechecks key conflicts and order uniqueness within `BEGIN IMMEDIATE`, so simultaneous attempts cannot bypass the application-level read. The request and outbox insert commit together. These guarantees are tested with separate connections, simultaneous workers, and an injected failure at the outbox insert.

Orders are immutable through the provided API. Code that modifies the SQLite file directly is outside that contract. Adding mutable order state, currency conversion, authorization, or an external payment worker introduces new contracts and failure modes; the current test results do not cover them.

## What is checked

- Policy boundaries: before payment, exactly at payment, just before 30 days, exactly at 30 days; allowed states; aware timestamps; integer cents.
- Ledger contracts: durable request plus event, replay, conflicting key, second key for one order, missing order, wrong amount, rollback when the outbox insert fails, and concurrent requests.
- Manifest integrity: files and named Python symbols exist, task owners belong to the declared context and scope, checks resolve to test methods, and effects/bindings reference existing symbols.
- Dependency constraints: all production modules are declared, static imports stay within an explicit allowlist, and wildcard imports plus direct `eval`, `exec`, and `__import__` calls are rejected.
- Receipt behavior: changed source or observed Git revision invalidates a receipt; failed tests, missing or skipped required checks, and observed changes during verification cannot produce a passing result. Each declared check needs an observed runtime success; aggregate unittest exit status alone is insufficient.

The import check is intentionally narrow. It does not prove purity or discover arbitrary reflective calls, file access, runtime dispatch, or every effect. A valid binding reference establishes that the named symbols exist; it does not prove that an arbitrary implementation satisfies its prose contract. Tests exercise the configured adapter's behavior. This example's manifest is a local format, not a universal AGENT schema.

## Prove that checks can reject known faults

`python tools/negative_controls.py` copies the example into temporary directories. For each control it first runs the original targeted test, then introduces a known fault and requires failure for the expected reason:

| Fault | Expected rejection |
|---|---|
| Change the refund boundary from `<` to `<=` | The exact-expiration test fails |
| Import `sqlite3` in the domain | The dependency check reports the forbidden edge |
| Point the task owner to a nonexistent function | Manifest validation reports a missing symbol |
| Commit the request before inserting its outbox event | The injected-failure test finds a surviving request |
| Remove `unittest.TestCase` inheritance from policy tests | The gate reports declared checks missing from discovery |
| Skip the policy test class | The gate reports required checks without runtime success |
| Change the policy while retaining same-size, same-timestamp stale bytecode | The verifier executes the changed source and catches the boundary failure |

All mutations happen in disposable copies. Seven rejected faults establish sensitivity to those seven faults; they are not a mutation-coverage score or a completeness claim.

## Revision-bound local evidence

`verify.py` hashes each scoped file, records the observed Git `HEAD` and working-tree state, validates the manifest and graph independently, requires a nonempty discovered suite containing every declared invariant check, runs that suite, and compares hashes and Git observations before and after. A passing receipt includes the file-hash map, canonical tree hash, exact commands, return codes, output hashes and logs, Python version, per-check execution inventory, and result. Every declared check must report runtime success; skip and expected-failure results do not discharge the obligation. The file inventory excludes `.git`, `__pycache__`, and Python bytecode; an unexpected file otherwise becomes part of the measured inputs. Symlink files and directories in the measured scope are rejected. Child checks use a fresh temporary bytecode-cache prefix so existing `.pyc` files cannot substitute previously cached code for measured source.

The content hash identifies uncommitted inputs as well as committed ones. `observed_git_head` is the repository revision observed during execution, **not a claim that the checked working tree equals that commit**. Committing a change makes a previous receipt stale even when scoped file contents stay the same. Generate fresh evidence for the revision actually being evaluated.

The receipt is unsigned and produced by the same local process as the checks. It is useful for detecting accidental stale evidence, but it is forgeable and cannot independently establish provenance. `--check-receipt` only compares an existing observation with current files, revision, and Python version; it does not rerun checks or authenticate the recorded results. Matching the version string does not establish an identical interpreter binary, operating system, or environment. Pre/post hashing cannot catch a file changed and restored during execution. A trusted CI implementation needs an immutable checkout, controlled check definitions, an independently reported result, and an explicit environment/dependency identity.

## What this demonstrates, and what still needs a benchmark

This reference makes a few claims executable: a known owner resolves, a forbidden dependency fails, boundary regressions are caught, an atomicity violation is caught, and stale evidence is rejected. These are measured checker outcomes, not measurements of coding-agent success, tokens, cost, or navigation accuracy.

To test those outcomes, compare behaviorally equivalent implementations under the same real maintenance tasks, agent/model version, tool budget, and independent hidden checks. Measure successful changes first, then context retrieved, tool calls, retries, total cost, and maintenance overhead. Do not count this project's extra manifest or verifier as a performance benefit without that experiment.

## License

Code in this example is covered by the repository's [MIT code license](../../LICENSE-CODE). This documentation is covered by [CC BY 4.0](../../LICENSE).
