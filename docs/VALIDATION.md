# Executed validation

Recorded: 2026-10-05. Local runtime: Python 3.12.14. These results validate the reference mechanisms, not the performance hypothesis about coding agents.

## Reference result

The local verifier completed with **28 named tests passing**, zero skipped required checks, and no failed or missing required checks. The demo persisted one refund request and one outbox event; an idempotent replay returned the original request.

The measured example-content digest was:

```text
34ecc6e654279e381c7d605a2b71736b24108be8c85267676a3cc8a6efb23c97
```

This digest uses the inventory and canonical encoding implemented in `examples/reference/verify.py`. It covers that example's files, including its tests and documentation, and excludes declared cache artifacts. It does not identify the whole repository or certify the execution environment. Generate a fresh receipt for a different revision or content set.

## Negative controls

All **seven** targeted controls first passed their baseline and then rejected a deliberate fault for the expected reason. They modified disposable copies; the live source digest remained unchanged.

| Deliberate fault | Observed detector |
|---|---|
| Inclusive expiration boundary | Boundary behavior test |
| Storage import in the domain module | Declared dependency check |
| Missing policy-owner symbol | Manifest reference validator |
| Commit before the outbox insert | Atomicity test with injected outbox failure |
| Policy tests no longer discoverable | Required-check inventory |
| Required policy tests skipped | Executed-success inventory |
| Changed source with same-size/same-mtime stale bytecode | Fresh-cache verification rejects the behavioral regression |

## Adversarial review and repairs

Independent review found four real faults in the initial example: undiscovered or skipped checks could appear successful; bytecode could differ from hashed source; a daylight-saving transition could change eligibility after serialization; and symlink directories could be omitted from the input fingerprint.

The final recheck confirmed the repairs, including runtime skips, expected failures, and skipped subtests blocking a required check; isolated bytecode caches; UTC elapsed-time comparison consistent through SQLite; and explicit rejection of symlink directories.

These outcomes demonstrate why checks themselves need negative controls. They do not establish resistance to a malicious implementer who can rewrite the verifier, completeness of the manifest, or coverage of arbitrary reflection and runtime effects.

## Reproduce

From `examples/reference`:

```sh
python demo.py
python tools/context.py refund-window
python verify.py --receipt /tmp/agent-reference-receipt.json
python verify.py --check-receipt /tmp/agent-reference-receipt.json
python tools/negative_controls.py
```

The [CI workflow](../.github/workflows/verify.yml) runs the reference and measurement-tool checks on Python 3.11, 3.12, and 3.13. Consult the actual run result for the target commit; the local result above does not stand in for a CI result.

## Not measured

No controlled agent-maintenance trial, token-saving result, cross-model improvement, or production-payment guarantee is reported. The benchmark tooling validates records and calculates descriptive measurements; synthetic fixtures test that tooling only. The next evidence step is to preregister and execute the [proposed comparison protocol](../benchmarks/PROTOCOL.md).
