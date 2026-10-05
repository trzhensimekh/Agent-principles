Prompt-derived common acceptance evaluator
========================================

The evaluator authors read only the four tasks/*.md prompts. Candidate code,
architecture guidance, implementation discussions, and candidate test outputs
were not used to write these suites. Pricing tests were authored by a separate
evaluator subagent under the same restriction.

This is procedural separation of held-out prompts and evaluation work. It is
not operating-system isolation: all agents share the workspace, and candidate
code executes with the permissions of the calling process. The evaluator does
not assert that filesystem access was prevented.

Usage (one fresh Python process for each invocation):
  python evaluator/runner.py --domain inventory --stage 1 --arm PATH
  python evaluator/runner.py --domain inventory --stage 2 --arm PATH
  python evaluator/runner.py --domain pricing --stage 1 --arm PATH
  python evaluator/runner.py --domain pricing --stage 2 --arm PATH

PATH must directly contain inventory.py or pricing.py. Stage 1 loads only the
initial requirements. Stage 2 runs initial and extension requirements together.
The sole stdout payload is JSON with test counts, failure/error test IDs and
tracebacks, captured candidate stdout/stderr, source hashes, and success status.
Exit code 0 means every selected test passed; exit code 1 means failure/error.
Subtests provide diagnostic parameter cases; tests_run counts test methods.

The --list option loads test definitions without loading candidate code and can
be used without --arm. It reports expected method counts and IDs, not results.

SHA256SUMS freezes the source tests, runner, and this protocol before the first
candidate run. Verify from the evaluator directory with sha256sum -c SHA256SUMS.
Do not revise the evaluator in response to an arm's output. Any later revision
must be disclosed and applied to all arms with a separate result set.
