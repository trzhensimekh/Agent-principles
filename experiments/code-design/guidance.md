# AGENT source-code design guidance

Apply these principles when choosing the implementation's code structure. Use ordinary language features. Do not create repository maps, agent manifests, verification receipts, or generic frameworks merely to satisfy the principles.

A — Atomic Context: Keep one policy decision's inputs, units, invariant, and failure behavior understandable together. Give the decision one clear name and authority. Split modules where a real contract lets a reader stop; do not fragment a rule across forwarding wrappers just to shorten files.

G — Graph Explicitness: Make execution paths and dependencies visible in function arguments, imports, and explicit composition. Give orchestration an obvious entry point. Avoid hidden global dependencies, string-based dispatch, and implicit hooks unless the required variation justifies them and the binding is explicit.

E — Economic Abstraction: Introduce an abstraction when its stable contract removes more reasoning than its indirection adds. Prefer direct domain operations to speculative generic engines. Preserve a useful abstraction that hides real repeated complexity; do not optimize for the fewest functions or lines.

N — Narrow Change Surface: Give each mutable resource and invariant a clear semantic owner. Do not duplicate business policy across callers. Keep representation private; expose operations that preserve invariants. Arrange likely policy changes behind stable boundaries, without hiding legitimately coupled changes or concentrating unrelated behavior in one god object.

T — Testable Behavior: Express decision logic as deterministic transformations of explicit inputs where practical. Keep time, randomness, storage, and external effects at explicit boundaries. Define and test failure, retry, and state-transition behavior. Test observable results and preserved invariants; do not rely on tests that merely mirror private implementation steps.

These rules guide code design; no particular class, function, directory count, inheritance ban, or mandated dependency-injection framework follows from them. Resolve tradeoffs using the stated task. Optimize correctness first.
