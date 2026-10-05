# AGENT — principles for agent-written code

Version 0.3 · Experimental · 2026-10-05

AGENT tells a coding agent how to choose and express software structure. Its subject is the source code being written: decisions, dependencies, abstractions, state, and observable behavior. Its intended maintainer is a fresh agent that must work without the original author's conversation or unstated assumptions.

The objective is to make correct implementation and future changes require less reconstruction. This is a design hypothesis with [supporting research](RESEARCH.md) and [experiments](experiments/README.md); no universal improvement follows from applying five labels.

The property being investigated is **agent legibility**: whether a fresh coding agent can recover enough correct meaning from a system to locate, explain, change, and verify its behavior under stated constraints. Legibility is the goal; these principles are proposed causes, not its definition or a validated scoring system. The [operational model](docs/LEGIBILITY.md) separates locating evidence, recovering semantics, predicting effects, and checking outcomes. Passing a task alone does not show which of these improved.

The principles do not prescribe an application framework, a language, a directory tree, a graph database, a context manifest, or a verification service. Existing tools can help measure the result. The properties must live in the code and its contracts.

The design unit is a semantic responsibility: a decision, invariant, algorithm, or protocol. Improving reconstructability must preserve the system's security, compatibility, latency, resource, and availability requirements.

## The five rules

| | Principle | Design object | Core rule |
|---|---|---|---|
| **A** | Atomic Context | The meaning that must be recovered | Keep a semantic decision coherent and locally understandable. |
| **G** | Graph Explicitness | Dependencies and execution paths | Expose how inputs become decisions and effects. |
| **E** | Economic Abstraction | The usefulness of a boundary | Hide more reasoning than the abstraction adds. |
| **N** | Narrow Change Surface | State, invariants, and impact | Assign owners that contain expected change and preserve invariants. |
| **T** | Testable Behavior | Observable semantics | Make important outcomes and failure obligations executable. |

These concerns overlap, just as other design principles do. A addresses what must be read; G addresses the relationships that must be followed; E judges whether a boundary earns its cost; N controls what must change together; T supplies a way to challenge an implementation.

E also governs tradeoffs among the other principles; these are not five independent measurement axes.

## A — Atomic Context

**Keep the inputs, policy, invariants, and failure semantics of one decision understandable together.**

When writing a rule, give it a domain name and an authoritative home. Place the relevant units, valid states, boundary conditions, and error behavior in that unit or its explicit contract. Let callers rely on a boundary instead of rediscovering its internals.

An atomic context is a cohesive unit of meaning. It need not be one function, class, or file, and it has no fixed token limit. Different decisions can belong in the same module when they share an invariant; one large workflow can contain several independent decisions.

### Apply it in code

- Express a refund's eligibility in one policy rather than distributing it across a route, serializer, and job.
- Name amounts and durations with their units. Make representation assumptions explicit.
- Keep rejection rules as visible as the happy path.
- Split an operation only when the extracted concept gives the reader a useful contract, not merely a shorter file.

```python
# Understanding a rule requires reconstructing hidden defaults and dispatch.
def eligible(order):
    return registry.policy(order.kind).allows(order, settings.current())

# The owner makes the decision and its boundary visible.
def refund_eligible(state, paid_at_utc, now_utc, window):
    elapsed = now_utc - paid_at_utc
    return state in {"paid", "shipped"} and timedelta(0) <= elapsed < window
```

This sketch assumes validated UTC timestamps and imports `timedelta` from `datetime`. A production boundary must establish those assumptions. Naming them is not validation.

**Ask before extracting:** what meaningful fact can the caller stop knowing?

**Failure mode:** many tiny wrappers make the decision harder to reconstruct. The opposite failure is combining unrelated policies into one enormous unit. Duplicate neither shared authoritative facts nor independently changing business rules merely to satisfy a file-layout preference.

**Experiment:** give a fresh agent a policy change. Observe missed constraints, necessary reading, and correctness. Small files alone do not count as success.

## G — Graph Explicitness

**Make dependencies, execution order, and relevant effect paths recoverable from ordinary source.**

Pass dependencies through parameters or constructors. Compose implementations in a visible place. Express orchestration through named operations. Use language and framework mechanisms that expose application-specific bindings instead of relying on unstated conventions.

The graph exists in the calls, imports, types, schemas, and wiring. A separate diagram can help, but it cannot compensate for code whose actual behavior contradicts it.

### Apply it in code

```java
// A hidden dependency must be discovered at runtime.
Receipt pay(Order order) {
    return Services.resolve("payments").charge(order);
}

// The dependency is part of the object's contract.
final class Checkout {
    private final PaymentGateway payments;

    Checkout(PaymentGateway payments) {
        this.payments = payments;
    }

    Receipt pay(Order order) {
        return payments.charge(order);
    }
}
```

Also make meaningful effect order visible. A `save()` that silently sends email through a hook creates an obligation the caller must discover. A named operation that records a transaction and an outbox event makes that obligation easier to inspect. Its storage contract must still guarantee the required atomicity.

**Ask before hiding a call:** how will the next agent discover that this operation reads state, selects an implementation, or causes an effect?

**Failure mode:** explicit-looking code can still lie about actual behavior. Static imports omit dynamic dispatch, configuration, events, and external consumers. Dynamic systems remain valid; expose the selection or registration boundary and state what cannot be resolved statically.

**Tradeoff:** familiar framework conventions can be cheaper than custom wiring. Do not flatten every library into application code. Expose the decisions that are specific to this system.

**Experiment:** ask a fresh agent to trace an operation and predict the effects of a change. Compare with execution and relevant consumer checks.

## E — Economic Abstraction

**Introduce an abstraction when its contract removes more understanding and coordination work than its indirection creates.**

A useful abstraction lets a caller ignore stable complexity. It may hide a large implementation behind a small trustworthy interface. An expensive abstraction adds concepts, configuration, navigation, or implicit state without allowing the caller to stop reading.

This is neither a ban on abstraction nor a rule to minimize classes. Reuse, isolation from vendor APIs, stable contracts, and genuinely repeated variation can justify a boundary even with only one implementation.

### Apply it in code

```python
# Several concepts must be reconstructed for one domain operation.
result = engine.execute("refund", Context(order=order, mode="full"))

# The operation's intent and dependencies are directly available.
result = request_full_refund(order_id, request_id, now, ledger)
```

Use a generic engine when its actual variation makes it worthwhile. Do not build it solely because future use cases might exist. Conversely, extracting a reusable integer-allocation algorithm may remove repeated reasoning even when the surrounding workflows differ.

Do not conflate similar syntax with shared policy. Two identical predicates can encode decisions that will change independently. Merging them can increase future coupling.

**Ask before adding a layer:** which details can its users reliably stop knowing, and which new concepts must they learn?

**Failure mode:** deleting a useful interface can spread storage representation into every caller. Excessive deduplication can replace clear domain decisions with a configuration language harder than the original code.

**Experiment:** compare actual implementation and follow-up tasks. Count correctness first, then navigation, retries, coupling, and upkeep. No static linter can prove that an abstraction pays for itself across unknown future tasks.

## N — Narrow Change Surface

**Give each important invariant and mutable resource a clear owner; place expected variation behind that boundary.**

Expose operations that preserve state rules. Keep representation private. Make related updates occur under the consistency contract that actually covers them. Callers should request a semantic transition rather than coordinate low-level writes themselves.

```python
# The caller owns neither the state nor the concurrency rule.
available = inventory.read_available(sku)
if available >= quantity:
    inventory.write_available(sku, available - quantity)

# The inventory boundary owns validation and reservation semantics.
reservation = inventory.reserve(request_id, sku, quantity)
```

In a concurrent system, `reserve` must enforce the invariant atomically. In a distributed system, it must specify the relevant consistency, idempotency, and conflict behavior. A name cannot create those guarantees.

### Apply it in code

- Return immutable values or defensive snapshots rather than unrestricted aliases to internal mutable state.
- Place state transitions and their validation under the same semantic owner.
- Keep database encoding and protocol representation behind boundaries when callers need domain meaning.
- Give a shared business decision one authority, while allowing legitimately different policies to vary separately.
- For a schema or event change, include the consumers and migration that actually share the contract.

One authority does not mean one occurrence of every check. Separate trust boundaries can require repeated validation. Independent acceptance tests should derive expected behavior from the requirement, not reuse the production helper or policy constant being checked; otherwise one wrong value can make implementation and oracle agree.

**Ask before exposing a field:** which invariants could another caller violate by changing it directly?

**Failure mode:** one global service owning everything becomes a bottleneck. Choose owners around invariants, not arbitrary file boundaries or the whole product. Distributed multiple-writer designs require explicit merge and conflict rules; they are not forbidden.

**Tradeoff:** a narrow textual diff can have global semantic impact. Do not minimize the number of files at the expense of a required consumer update or migration.

**Experiment:** change a policy, representation, or retry path and check every affected contract. Parallel agents can conflict through assumptions even when their edited files differ.

## T — Testable Behavior

**Express important behavior through explicit inputs, outcomes, state transitions, and effect obligations that can be exercised.**

Prefer deterministic policy over explicit data where practical. Supply time, randomness, configuration, and effect dependencies at meaningful boundaries. Preserve integration tests for the real behavior hidden by those boundaries.

```python
# Time is hidden inside the rule.
def expired(reservation):
    return time.monotonic() >= reservation.expires_at

# An exact boundary can be tested without waiting.
def expired(reservation, now):
    return now >= reservation.expires_at
```

A storage or network operation cannot become deterministic by ignoring its environment. Specify allowed outcomes and make the relevant failures observable. Test the actual adapter when its semantics matter.

### Apply it in code

- Keep calculation separable from unrelated persistence when that creates a useful boundary.
- Represent failures with clear domain exceptions or result variants; do not overload an ambiguous boolean.
- Define retry, timeout, cancellation, duplicate delivery, and ordering behavior where relevant.
- State which operations are atomic, which may be repeated, and which require recovery or compensation.
- Assert observable outcomes and invariants rather than a fragile sequence of private method calls.

**Ask while implementing:** what small execution would refute my understanding of this rule?

**Failure mode:** mocks can erase the integration behavior that needs testing. Generating tests from an incorrect implementation can merely restate the same mistake. Use independently stated requirements, boundary cases, and meaningful negative controls.

**Tradeoff:** do not introduce an interface for every pure function. Use the lightest mechanism that makes the obligation executable. Asynchronous systems need tests for permitted outcomes, not a false promise of exactly-once delivery or a single deterministic schedule.

**Experiment:** test initial behavior and previously withheld changes, then inject selected faults. A passing test suite establishes its checked scope, not the completeness of the requirements.

## Resolve conflicts between principles

A cohesive unit can become too large; an extraction can increase navigation. An explicit dependency can expose unnecessary details; a useful abstraction can hide unstable behavior. Local state ownership can simplify reasoning while making a distributed workflow require coordination.

Resolve those tensions around the actual invariant and expected change. Prefer a contract that permits local reasoning over either extreme: one large function that exposes everything, or many small abstractions that hide nothing useful. When evidence contradicts the expected benefit, change the design rather than defending the acronym.

No principle mandates a fixed file size, language paradigm, inheritance depth, class count, or token budget. A familiar library with a good contract can be cheaper for an agent than a bespoke implementation.

## Relationship to SOLID and earlier AGENT versions

SOLID supplies useful rules about responsibilities, extensibility, substitution, interface scope, and dependency direction. AGENT emphasizes the code a bounded-context autonomous maintainer must reconstruct and modify. The foundations overlap; the proposed contribution is the combined coding guidance and its evaluation against agent work.

The v0.1 names were Atomic Context and Testable Architecture. v0.2 explored Addressable Context and Traceable Verification, along with a verification profile. v0.3 restores **Atomic Context** as a semantic code-design property and uses **Testable Behavior** to focus on the implementation's observable semantics. Addressability, graphs, and receipts remain possible supporting mechanisms. The [v0.2 verification profile](docs/VERIFICATION-PROFILE.md) is preserved separately.

Read the [coding guide](GUIDE.md), [design decisions](docs/DESIGN-DECISIONS.md), [research](RESEARCH.md), [prior art](docs/PRIOR-ART.md), and [experiments](experiments/README.md). Use the [larger evaluation protocol](benchmarks/PROTOCOL.md) for claims beyond the exploratory study.
