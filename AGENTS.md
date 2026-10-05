# Working on AGENT Principles

Use English for repository content and commit messages.

Start with [README.md](README.md). Normative proposal: [SPECIFICATION.md](SPECIFICATION.md). Evidence and limitations: [RESEARCH.md](RESEARCH.md).

Keep empirical findings, engineering recommendations, and untested hypotheses distinct. Link primary sources next to claims. Do not claim token savings or improved agent success without a controlled trial and raw results.

The reference implementation and its commands live in [examples/reference/README.md](examples/reference/README.md). Benchmark protocol and tools live in [benchmarks](benchmarks).

Change code and relevant contracts together; run the affected checks. Do not weaken a detector to make a negative control pass. Keep credentials, conversation transcripts, temporary receipts, caches, and generated local databases out of commits.

Text is CC BY 4.0; original code and executable examples are MIT. Preserve attribution and the explicit limits of the local verifier.
