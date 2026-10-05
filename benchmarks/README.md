# Benchmark status and tools

**No empirical AGENT performance experiment has been run.** Read [PROTOCOL.md](PROTOCOL.md) before designing one. The analyzer validates data shape and calculates descriptive paired summaries; it does not run agents, verify task acceptance, detect fabricated input, or infer statistical significance.

```sh
python benchmarks/analyze.py benchmarks/synthetic.jsonl --allow-synthetic
python -m unittest discover -s benchmarks/tests -v
```

`synthetic.jsonl` contains deliberately invented test data. It is a software fixture, not evidence for AGENT. The fixture includes failed and retried attempts and a case where the AGENT arm performs worse. Synthetic inputs are rejected unless explicitly enabled, and cannot be mixed with observed inputs.

Each JSONL record describes one episode, identified by `repository`, `task`, `model`, `repeat`, and `variant`. Both `baseline` and `agent` records must exist for every repository/task/model/repeat. Model strings should identify the frozen model and scaffold configuration; use a separate file for each experimental contrast. `repeat` is a nonnegative integer. `origin` is `observed` or `synthetic`.

`attempts` is a nonempty list. Each attempt requires a boolean `success` from the independent acceptance oracle and a finite nonnegative `cost_usd` that includes all declared charges for that attempt. The record's success is whether any budgeted attempt succeeds; all attempts are charged. This supports a preregistered retry or best-of-N policy; the analyzer cannot check that the policy was followed. Optional nonnegative integer fields are `input_tokens`, `cached_input_tokens`, `output_tokens`, and `tool_calls`. Treat input and cached input as separate counts, not overlapping totals. If a usage field is missing in any attempt, its aggregate is `null` instead of an invented zero.

`cost_usd` is a required externally computed total under the registered accounting policy. Amortized indexing, migration, infrastructure, and other shared costs must be allocated consistently before ingestion and documented in the manifest. This compact schema cannot reconstruct them. Store detailed invoices, pricing dates, reasoning-token availability, failure categories, environment hashes, wall times, patches, and verification receipts in the experiment's immutable raw artifacts. Preserve unrounded costs in input.

The output includes success rates, failed attempts, total cost per success including failures, paired agent-minus-baseline deltas, model breakdowns, repository breakdowns, and a repository-balanced descriptive average. Cost per success is `null` when there are no successes. The pooled summaries give equal weight to each paired episode; repository-balanced summaries give equal weight to each repository and then average its episodes. Unequal task/repeat counts therefore change the former weighting. Neither is automatically the correct population estimand: preregister weighting and balance the design.

No confidence intervals are produced. In particular, repeats do not count as independent repositories. Missing pairs cause failure instead of silent exclusion. A study must retain resource-exhausted failures as observations; only registered infrastructure exclusions may be handled outside this tool with a published audit trail.
