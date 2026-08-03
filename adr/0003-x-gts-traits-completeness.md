# ADR-0003: `x-gts-traits` completeness — when required traits must be resolved

- **Status:** Accepted
- **Date:** 2026-05-27
- **Deciders:** GTS spec maintainers
- **Consulted:** —
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

GTS types carry trait values via `x-gts-traits` against a trait-schema declared in `x-gts-traits-schema` (per ADR-0002). The trait-schema may declare some properties as `required`. The spec must decide what happens to those required properties when they are not resolved — neither explicitly assigned by `x-gts-traits` along the type's `$id` chain, nor covered by a `default` in the effective trait-schema.

### How completeness arises

A GTS type's `x-gts-traits` provides concrete values for the trait properties declared by `x-gts-traits-schema`. Trait-schemas (per ADR-0002) compose along the `$id` chain via `allOf` to produce an *effective trait-schema*. Trait values compose along the same chain to produce an *effective traits object*. When the effective trait-schema marks a property as `required`, the effective traits object must satisfy that requirement somehow — otherwise the type's trait surface is, in JSON Schema terms, invalid.

### What the spec must decide

- Whether GTS enforces completeness at all (or leaves it to authors / runtime).
- If yes, at what moment the check fires.
- For which types the check fires.
- What counts as "resolved" — does `default` in the effective trait-schema satisfy `required`, or only explicit values?

### Why this matters

Two scenarios bite if the spec stays silent. (a) A type that ships values for some traits but leaves a required one unset registers without complaint; downstream consumers see "missing retention" / "missing topic-ref" at runtime, with no visible error at registration. (b) An abstract base type that declares a required trait field with no default has no way to remain abstract — it can never satisfy its own required surface, and the spec has no carve-out for "incomplete by design."

### Worked example to anchor the question

Consider a base event type that declares a required `retention` trait with no default:

```jsonc
// Base event type
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~",
  "type": "object",
  "required": ["id", "occurredAt"],
  "properties": {
    "id":         { "type": "string" },
    "occurredAt": { "type": "string", "format": "date-time" }
  },
  "x-gts-traits-schema": {
    "type": "object",
    "required": ["retention"],
    "properties": {
      "retention": { "type": "string" }
    }
  }
}
```

A vendor registers a derived event type without supplying a `retention` value:

```jsonc
// Derived event type — no x-gts-traits at all
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~vendor.order_placed.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "required": ["orderId"],
  "properties": {
    "orderId": { "type": "string" }
  }
}
```

The effective trait-schema for `order_placed.v1~` (per ADR-0002) requires `retention`. The effective traits object is empty. The required field is unresolved. **Should this registration succeed or fail?** The answer depends on:

- whether GTS enforces completeness at all (Option 1 says "no rule");
- if so, whether the check fires now or later (Option 2 vs Option 3);
- whether the derived type's modifier matters (a non-abstract derived type ≠ an abstract derived type).

Three variants of the same example clarify what's at stake:

- *Variant A — base declares a default:* if `x-gts-traits-schema.properties.retention` has `"default": "P30D"`, the required field is satisfied by the default. The derived type can register without writing `x-gts-traits`.
- *Variant B — derived type supplies the value:* the derived adds `"x-gts-traits": { "retention": "P90D" }`. Required is resolved.
- *Variant C — derived type marks itself abstract:* `"x-gts-abstract": true`. The type declares "I am intentionally incomplete; my descendants close `retention`." Whether to accept this depends on the option chosen.

### The framing this ADR inherits

ADR-0001 commits GTS to being an extension of JSON Schema (dialect-agnostic); ADR-0002 says `x-gts-traits-schema` is an ordinary JSON Schema subschema with chain aggregation at the registry. The completeness rule follows the same philosophy: use standard JSON Schema mechanisms where possible, add a minimum of GTS-specific policy on top.

## Decision Drivers

- **Fail fast.** Errors should surface at registration time, not at instance creation or at runtime, when affordable.
- **Respect abstract intent.** Abstract types are explicitly "incomplete waiting for descendants"; the rule must accommodate this.
- **No registry-state-dependent rules.** Whether a type is currently a "leaf" depends on which descendants happen to be registered. Tying the completeness rule to that property creates post-hoc invariants — registering a descendant could retroactively change whether the ancestor was "supposed to be" complete. Avoid.
- **Ergonomics for the common case.** A required trait with a sensible `default` should not force the author to write a redundant `x-gts-traits` entry just to "explicitly satisfy" required.

## Considered Options

- Option 1 — No spec-level enforcement (author's responsibility)
- Option 2 — Validate at instance creation time
- Option 3 — Validate at type registration (fail fast) *(chosen)*

Three top-level options on **when (or whether) to enforce completeness**.

### Option 1 — No spec-level enforcement (author's responsibility)

The spec describes how `x-gts-traits` and `x-gts-traits-schema` work, but says nothing normative about required-trait satisfaction. If a non-abstract type registers with unresolved required traits, that's the author's bug, surfaced (if at all) by downstream tooling or by runtime failures.

- **+** Smallest spec footprint. No new operation, no new failure mode.
- **−** Defers a real correctness problem to runtime. A type that *looks* well-formed at registration can break downstream consumers at any later point. No clear contract for what "valid trait surface" means.
- **−** The `required` keyword in `x-gts-traits-schema` becomes effectively informational — it tells consumers "this matters" but the registry doesn't check anything. Encourages divergence between implementations.

### Option 2 — Validate at instance creation time

Type registration is permissive: any non-abstract type may register with an incomplete trait surface. When an instance is registered against such a type, the registry computes the type's effective traits and rejects the instance registration if required traits are unresolved.

- **+** A type-author can publish work-in-progress non-abstract types without immediately providing values for every required trait; descendants or the same type's later updates can close gaps before any instance ever exists.
- **+** No new failure mode at type registration.
- **−** Late failure — the broken trait surface goes undetected from type registration until the first instance is registered, which could be much later, against a different operator, on a different system. Hard to diagnose.
- **−** Asymmetric with type-side validation already enforced at registration (structure, derivation compatibility per OP#12, finality guard per §9.11.2, trait-schema satisfiability per ADR-0002).
- **−** An incomplete non-abstract type that someone never instantiates sits in the registry indefinitely as a latent defect. The `x-gts-abstract` modifier already serves the "intentionally incomplete" use case — there is no separate need for "non-abstract but also incomplete".

**Concrete example.** Reusing the base event type from the worked example above (required `retention` trait, no default):

```jsonc
// Non-abstract derived type — no x-gts-traits, no x-gts-abstract.
// Under Option 2: registration SUCCEEDS (completeness is not checked at type time).
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~vendor.order_placed.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "required": ["orderId"],
  "properties": { "orderId": { "type": "string" } }
}
// → Registration accepted. Type sits in the registry with an unresolved
//   required trait.

// First instance of this type, registered some time later.
{
  "id":         "evt-001",
  "occurredAt": "2026-05-27T12:00:00Z",
  "orderId":    "ord-7"
}
// → Instance registration FAILS: required trait `retention` unresolved on
//   gts://gts.x.example.event.v1~vendor.order_placed.v1~.
//   The defect surfaces at the first instance — possibly long after the
//   type was registered, in a different system or by a different operator.
```

### Option 3 — Validate at type registration (fail fast) *(chosen)*

At type registration, the registry computes the effective trait-schema and effective traits object for the new type. For **non-abstract** types, the registry MUST verify that every required property in the effective trait-schema is resolved — either by an explicit value in the chain-merged `x-gts-traits`, or by a `default` declared in the effective trait-schema. For **abstract** types, this check is skipped — abstract types are by definition "incomplete waiting for descendants."

- **+** Fail fast at the obvious correctness boundary. By the time a non-abstract type is in the registry, any instance against it is guaranteed to find a complete trait surface — no separate check at instance time needed.
- **+** `x-gts-abstract` already exists for the "intentionally incomplete" case; this option uses it as the natural escape hatch instead of inventing a separate carve-out.
- **+** No notion of "leaf" required. Whether the type has descendants now or later is irrelevant — the rule is keyed on `x-gts-abstract`, which is a property of the type itself.
- **+** Symmetric with other registration-time validations (structure, OP#12 derivation compatibility, OP#13 trait-schema satisfiability).
- **−** Authors of mid-level types who want to publish "non-abstract scaffolding with required traits TBD" must either provide stub `default` values, provide stub `x-gts-traits` values, or mark the type abstract. In practice this is the right pressure — incomplete-but-instantiable is a bug, not a feature.

**Concrete example.** Same base event type as above (required `retention` trait, no default):

```jsonc
// Non-abstract derived type with no x-gts-traits.
// Under Option 3: registration FAILS at type time.
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~vendor.order_placed.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "required": ["orderId"],
  "properties": { "orderId": { "type": "string" } }
}
// → Error: required trait `retention` unresolved on non-abstract type
//   gts://gts.x.example.event.v1~vendor.order_placed.v1~.
```

Three ways to make the registration succeed:

```jsonc
// (a) Supply the value directly on the derived type via x-gts-traits.
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~vendor.order_placed.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": "P90D" },
  "required": ["orderId"],
  "properties": { "orderId": { "type": "string" } }
}
// → OK: effective traits object = { retention: "P90D" }, satisfies required.
```

```jsonc
// (b) Declare a default in the base trait-schema (ripples to all descendants).
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~",
  "type": "object",
  "required": ["id", "occurredAt"],
  "properties": {
    "id":         { "type": "string" },
    "occurredAt": { "type": "string", "format": "date-time" }
  },
  "x-gts-traits-schema": {
    "type": "object",
    "required": ["retention"],
    "properties": {
      "retention": { "type": "string", "default": "P30D" }
    }
  }
}
// → All descendants that don't override `retention` materialize it to "P30D"
//   and pass the completeness check without writing x-gts-traits themselves.
```

```jsonc
// (c) Mark the derived type abstract — it opts out of the completeness check.
//     Concrete descendants will still have to resolve `retention`.
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~vendor.order_placed.v1~",
  "type": "object",
  "x-gts-abstract": true,
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "required": ["orderId"],
  "properties": { "orderId": { "type": "string" } }
}
// → OK: completeness check skipped for abstract types.
```

## Decision Outcome

Chosen option: **Option 3 — validate at type registration; non-abstract types MUST be complete.**

### Definition of "complete"

A GTS type T is **complete** iff the materialized effective traits object of T validates against the effective trait-schema of T using standard JSON Schema validation, where "materialized" means: for every property in the effective trait-schema that has a `default` and is not present in the chain-merged effective traits object, the `default` value is substituted in.

### Qualifier

The completeness check applies if and only if the type's `x-gts-abstract` is not `true` (i.e., the type is non-abstract). Final types (`x-gts-final: true`) are not a special case — they are non-abstract types, and the same rule applies. The "leaf" notion (registry-state-dependent absence of descendants) plays no role.

### Algorithm

At the registration of type T:

1. Compute *effective trait-schema* = JSON Schema `allOf` composition of all `x-gts-traits-schema` declarations along T's `$id` chain (per ADR-0002).
2. Compute *effective traits object* = chain-merged `x-gts-traits` along T's `$id` chain (per ADR-0004, RFC 7396 JSON Merge Patch root → leaf).
3. *Materialize* the effective traits object: for every property declared in the effective trait-schema with a `default` and no value in the merged object, substitute the default value.
4. If `T.x-gts-abstract` is `true`: skip the completeness check (other validations on T still run normally).
5. Otherwise: validate the materialized effective traits object against the effective trait-schema using standard JSON Schema validation. If validation fails (including `required` properties absent after materialization), registration MUST fail with an error citing the unresolved required properties.

### Edge cases this rule covers correctly

- **No traits anywhere in chain.** Effective trait-schema is empty / `true` / has no `required`. Materialized object validates trivially. ✓
- **`x-gts-traits-schema: false` somewhere in the chain.** This is the strong "no traits permitted" declaration. Derivation compatibility (per ADR-0002 / OP#12) requires the effective trait-schema of every descendant to be `allOf` of all `x-gts-traits-schema` along its chain, which includes `false`. Because `false` is the unsatisfiable schema and `allOf(false, anything) ≡ false`, the effective trait-schema of every descendant in the subtree is also `false` — descendants cannot "extend" or "override" it; they inherit the unsatisfiability. The consequence: **on the entire subtree rooted at the `false` declaration, traits are effectively banned**:
  - A non-abstract type in the subtree fails registration the moment it tries to provide any `x-gts-traits` value (or has a required to satisfy) — the only `x-gts-traits` that can validate against `false` is "no traits at all" together with no `required`, which `false` doesn't have.
  - In practice, the only way to register a non-abstract type under a `false` is to provide no `x-gts-traits` at all *and* have no required traits — which is precisely the "no traits, period" semantics the author signaled with `false`.
  - An abstract type in the subtree may exist (skips the check) but offers no useful path to descendants either, because every descendant will still inherit `false`.
- **Abstract base with required-no-default, non-abstract descendant supplies value.** Base registration skips the check (abstract). Descendant registration runs the check on its effective state; the descendant's `x-gts-traits` value satisfies the required field. ✓
- **Non-abstract type with required-no-default and no explicit value.** Registration fails. Author resolves by (a) providing `x-gts-traits` value, (b) declaring a `default` in the schema, or (c) marking the type abstract.
- **Final non-abstract type.** Same rule as any non-abstract — must be complete. No special bullet needed.

### Implications

- **OP#13 (Schema Traits Validation)** includes this rule; the operation explicitly conditions the completeness step on `x-gts-abstract != true`.
- **§9.7.5** carries the normative wording of the completeness check in the "Validation" bullet block, expressed in terms of "non-abstract types."
- **§9.11.4 (Interaction with `x-gts-traits`)** states the same rule via the modifier lens — keyed on `x-gts-abstract`, with the final case shown as a corollary.
- **`x-gts-traits` value validation** against trait-schema property constraints (independent of `required`) is unchanged; this ADR only adds the conditional `required` resolution check.
- **Reference implementations (gts-go, gts-rust)** must implement the materialization step and the conditional completeness check at type registration.
- **Backward compatibility.** The rule applies to any new registration. Existing registered types are evaluated against this rule on their next registration / re-registration; production registries SHOULD treat already-registered types as grandfathered until the next write.

## Pros and Cons of the Options

### Option 1 — No spec-level enforcement

- **+** Smallest spec footprint.
- **−** Defers a real correctness problem to runtime; `required` becomes informational only.

### Option 2 — Validate at instance creation time

- **+** Permits "work-in-progress" non-abstract types.
- **−** Late failure; asymmetric with other registration-time checks.
- **−** `x-gts-abstract` already covers the legitimate "intentionally incomplete" case so the extra permissiveness has no clear use.

### Option 3 — Validate at type registration (chosen)

- **+** Fail fast at the natural boundary; uses `x-gts-abstract` as the natural escape hatch.
- **+** "Leaf" notion drops out; rule is keyed on a property of the type itself.
- **+** Symmetric with other registration-time validations (OP#12, OP#13 trait-schema satisfiability, finality guard).
- **+** Defaults remain ergonomic — required-with-default does not force a redundant `x-gts-traits` entry.
- **−** Mid-level non-abstract types that genuinely want to leave a required trait open must mark themselves abstract (or supply stub defaults). In practice this is the right pressure.

## More Information

Cross-references inside this specification: §9.7 (`x-gts-traits-schema` / `x-gts-traits`), §9.11 (`x-gts-final` / `x-gts-abstract`), OP#13 (Schema Traits Validation). Related ADRs: [`adr/0001-derivation-form.md`](0001-derivation-form.md) (the extension framing), [`adr/0002-x-gts-traits-schema.md`](0002-x-gts-traits-schema.md) (effective trait-schema via chain aggregation — the input to the completeness check).

External references:

- [`required` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/object#required)
- [`default` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/annotations)
