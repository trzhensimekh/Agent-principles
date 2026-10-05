# Apply AGENT while writing code

Use the [compact guide](../GUIDE.md) with the task. The agent's output should be working, well-structured source code. Repository tooling is optional.

## 1. Identify decisions and invariants

List the actual domain decisions: eligibility, allocation, scheduling, state transitions, authorization, or compatibility. State what must remain true after each relevant operation. Distinguish a policy from a storage representation or transport detail.

Do not create architecture layers before identifying the decisions they would separate.

## 2. Choose semantic owners

Place a decision where its inputs, units, errors, and constraints can be understood together. Assign mutable state to operations that preserve its invariants. Choose functions, objects, modules, or services according to the required behavior.

A module split is useful when it gives callers a stable contract. A split that adds only navigation is a cost.

## 3. Shape the public contract

Make meaningful inputs, outputs, errors, and effects explicit. Validate at the appropriate boundary. State retry and partial-failure behavior where it matters. Keep representation private when exposing it would make callers coordinate the invariant.

An interface with one implementation may be justified around a complex external effect. Ten forwarding interfaces around a trivial calculation may not be.

## 4. Implement the straightforward path

Write domain operations with explicit orchestration. Introduce abstractions for real repeated meaning or variation. Avoid speculative registries, plugin engines, and generic context objects unless their capabilities are required.

Use familiar libraries and frameworks when their contracts reduce the amount another agent must reconstruct.

## 5. Make behavior challengeable

Where useful, calculate decisions from explicit inputs and perform effects through narrow boundaries. Supply clocks and randomness when they affect behavior. Test boundaries, invalid input, state transitions, and relevant retries or conflicts.

Then test the integration semantics the pure core cannot establish. Do not replace a database atomicity test with assertions that mocks were called in a preferred order.

## 6. Change the code with a fresh context

Give a new agent the task and repository, without the original author's conversation. Observe where it must reconstruct meaning, which assumptions it misses, and whether it preserves the contracts while implementing the new behavior.

Use those observations to improve code structure. Additional documentation can help with an otherwise unavailable fact; duplicating already discoverable code is not automatically beneficial.

## 7. Retain the evidence that affects design

Record reproducible failures and useful comparisons. The [exploratory experiment](../experiments/README.md) shows one way to test generation followed by a fresh-maintainer change. The [larger protocol](../benchmarks/PROTOCOL.md) is for stronger claims.

If a mechanism adds complexity without improving correctness or changeability, remove it. A design principle must survive contact with actual tasks.

For systems that need formal agent-to-agent evidence handoff, the optional [verification profile](VERIFICATION-PROFILE.md) describes additional controls. It is not required to apply the source-code principles.
