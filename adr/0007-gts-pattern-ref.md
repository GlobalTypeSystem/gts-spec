# ADR-0007: Pattern-valued fields — the `x-gts-pattern-ref` keyword

- **Status:** Accepted <!-- Accepted on merge, per CONTRIBUTING.md. -->
- **Date:** 2026-10-09
- **Deciders:** GTS spec maintainers
- **Consulted:** aviator5
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

Some fields hold GTS identifier patterns, such as access scopes (§3.5) or subscription interests like `gts.cf.core.events.event.v1~*`.

[`x-gts-ref`](../README.md#96---x-gts-ref-support) cannot describe these fields: in every validation mode, its value must be a concrete identifier. Consumers therefore copy the GTS grammar into `pattern` regexes, which drift from §2 and §10.

How should a schema declare a pattern-valued string and the family of identifiers it may select?

## Decision Drivers

- The specification defines the pattern grammar once.
- Express both "any valid pattern" and "a pattern within this family".
- Results independent of registry state.
- `x-gts-ref` unchanged.

## Considered Options

- Option 1 — Regex in each consumer
- Option 2 — Reuse or relax `x-gts-ref`
- Option 3 — Format with consumer constraints
- Option 4 — One keyword for syntax and coverage *(chosen)*
- Option 5 — Format plus a coverage keyword

### Option 1 — Regex in each consumer

Each consumer schema copies the GTS pattern grammar, and any family scope, into a standard `pattern`.

### Option 2 — Reuse or relax `x-gts-ref`

Use `x-gts-ref` for pattern-valued fields, or relax it so that its value may be a pattern.

### Option 3 — Format with consumer constraints

A `format: "gts-id-pattern"` checks pattern syntax; consumers add short `pattern`s for kind and family.

### Option 4 — One keyword for syntax and coverage

A keyword checks the syntax of its operand and value and requires the operand's scope to cover the value; the operand `gts.*` checks syntax only. It is named `x-gts-pattern-ref`, paralleling `x-gts-ref`; `x-gts-pattern` was considered as an alternative name.

### Option 5 — Format plus a coverage keyword

The format of Option 3 checks syntax, and a separate keyword checks coverage.

## Decision Outcome

Chosen option: "Option 4", because one keyword handles both syntax-only and family-scoped fields.

### Semantics

- **Operands.** The operand is a concrete GTS Type ID, a concrete GTS Instance ID, a wildcard pattern (§10), or exactly `/$id`. Other pointer forms and invalid operands are schema errors.
- **Effective self-reference.** `/$id` resolves to the canonical top-level `$id` of the effective leaf GTS Type Schema selected for validation, without `gts://`. That root is retained through inherited constraints, `$ref`, and `allOf`, as for `x-gts-ref` (§9.6); it is not the `$id` of the subschema containing the keyword. A missing or invalid selected identifier is a schema error.
- **Validity.** A string value must be a valid GTS identifier pattern and satisfy M(value) ⊆ M(operand), after resolving `/$id`. M(p) contains all canonical GTS identifiers selected by p under the literal and wildcard matching rules of §9.6 and §10, regardless of registration.
- **Matching.** A concrete Type ID selects itself and its descendants (`root~` ≡ `root~*`), with minor-version flexibility. A concrete Instance ID selects only that exact identifier, with no minor-version expansion. Wildcards follow §10: first-segment `v1.*` and `v1~*` are equivalent; in later segments, `v1.*` also selects instances.
- **Spelling.** The GTS grammar governs spelling and length: no trimming, case folding, or `gts://` stripping from field values; at most 1024 characters; no numeric limits beyond §2.3.
- **Applicability and errors.** Use the same property-value applicability, schema locations, traversal, and validation paths as `x-gts-ref` (§9.6), including array-item schemas and effective trait-schema properties. The keyword constrains strings only; schemas specify `"type": "string"` separately. Literal data is not scanned. An invalid or uncovered value is a validation error that `not` can invert; an invalid operand is a schema error and cannot be inverted.
- **No registry lookup.** `gts-ref-validation`, the §9.2 dependency closure, and OP#7 reference tracking do not apply.

Property schema accepting any valid pattern:

```json
{ "type": "string", "x-gts-pattern-ref": "gts.*" }
```

Property schema for patterns within the event family:

```json
{ "type": "string", "x-gts-pattern-ref": "gts.cf.core.events.event.v1~" }
```

A property whose pattern is scoped to the selected type:

```json
{
  "$id": "gts://gts.cf.core.events.event.v1~",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "selector": { "type": "string", "x-gts-pattern-ref": "/$id" }
  }
}
```

### Derivation and evolution

- **OP#12.** Keep the semantic rule of §4.1: Valid(derived) ⊆ Valid(base). `allOf` preserves inherited constraints by conjunction. For isolated positive constraints with literal operands, base covering derived proves narrowing; equivalent constraints and intersections may also establish it. Retaining a particular keyword spelling is not required. Resolve `/$id` for each effective schema being compared.
- **OP#8.** Compare the complete schemas under §4.3. For isolated positive constraints, widening the new operand is backward compatible, narrowing it is forward compatible, and equal scopes are fully compatible. `not` reverses those directions; compositions must be assessed as a whole. Report `unknown` when inclusion cannot be established.

### Implications

- README §9 defines the keyword, and §10 adds coverage to the pattern grammar. The specification and conformance suite implement this decision for 0.16.
- Conformance vectors cover syntax, exact instance matching, wildcard boundaries, minor versions, segment position, inherited `/$id`, traits, and compatibility through composition in every supported dialect. Coverage is checked over canonical identifiers, not registered matches.
- A format would be simpler to add to generic validators, while this keyword requires every implementation to compute coverage. That difference does not justify a second public mechanism.
- OP#12 narrowing for `x-gts-ref` is a separate follow-up.

## Pros and Cons of the Options

### Option 1 — Regex in each consumer

- **+** Works in any JSON Schema validator.
- **−** Duplicates the grammar in every consumer, and the copies drift.

### Option 2 — Reuse or relax `x-gts-ref`

- **+** Reuses an existing keyword.
- **−** Values must be concrete; relaxing that would change reference semantics and validation modes.

### Option 3 — Format with consumer constraints

- **+** Easy to add to generic validators.
- **−** Family scopes remain regexes that restate version and chain rules.

### Option 4 — One keyword for syntax and coverage

- **+** One mechanism covers syntax-only and family-scoped fields.
- **−** Every implementation must compute coverage.

### Option 5 — Format plus a coverage keyword

- **+** The format can be used on its own.
- **−** Two public mechanisms duplicate the syntax-only check.

## More Information

[README §9.6](../README.md#96---x-gts-ref-support) defines literal matching and selected-type self-reference; [README §10](../README.md#10-collecting-identifiers-with-wildcards) defines wildcards. [Issue #96](https://github.com/GlobalTypeSystem/gts-spec/issues/96) concerns the kind of concrete references; this keyword accepts pattern-valued properties and does not require an additional `pattern` constraint.
