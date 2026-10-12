# ADR-0007: Pattern-valued fields — the `x-gts-pattern-ref` keyword

- **Status:** Accepted <!-- Accepted on merge, per CONTRIBUTING.md. -->
- **Date:** 2026-10-09
- **Deciders:** GTS spec maintainers
- **Consulted:** aviator5
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

An access scope (§3.5) can pair an action, such as `read`, with a GTS identifier pattern that selects the resources to which the action applies. For example, a scope may select all resources, all storage buckets, or one particular bucket. If the scope is itself modeled as a GTS type, its JSON Schema needs to describe the field holding that resource pattern: both the allowed syntax and, where required, the resource family it may select.

Similarly, when creating a subscription to events, a client can pass a pattern such as `gts.x.core.events.event.*`; if the subscription is a GTS type, its schema must describe that pattern-valued field.

[`x-gts-ref`](../README.md#961-entity-references-x-gts-ref) cannot describe these fields: in every validation mode, its value must be a concrete identifier. Consumers therefore copy the GTS grammar into `pattern` regexes, which drift from §2 and §10.

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

The examples below use an access scope type with an `action` and a `resource_pattern`. For example, the bucket type `gts.x.core.resources.resource.v1~acme.storage.resources.bucket.v1~` derives from the resource type `gts.x.core.resources.resource.v1~`. The scope schema allows resource patterns across all versions of this resource family (`gts.x.core.resources.resource.*`). Each option supplies the schema for the `resource_pattern` property:

```json
{
  "$id": "gts://gts.x.core.iam.access_scope.v1~",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["action", "resource_pattern"],
  "properties": {
    "action": { "type": "string", "enum": ["read", "write"] },
    "resource_pattern": { "type": "string" }
  }
}
```

For example, an access scope payload allowing reads on storage buckets can contain:

```json
{
  "action": "read",
  "resource_pattern": "gts.x.core.resources.resource.v1~acme.storage.resources.bucket.*"
}
```

The scope's schema should allow patterns within the resource family, including a concrete instance identifier that selects just one resource:

| `resource_pattern` value | Result | Resource selection |
|---|---|---|
| `gts.x.core.resources.resource.*` | Accept | All versions of the resource type and all derived types and instances. |
| `gts.x.core.resources.resource.v1~` | Accept | This resource type and all derived types and instances, with minor-version flexibility within major version 1. |
| `gts.x.core.resources.resource.v1~acme.storage.resources.bucket.*` | Accept | All versions of the bucket type and all derived types and instances under resource major version 1. |
| `gts.x.core.resources.resource.v1~acme.storage.resources.bucket.v1~acme.prod._.uploads.v1` | Accept | One bucket instance, by its exact identifier. |
| `gts.x.core.resources.*` | Reject | Valid syntax, but a broader scope that can select identifiers outside the resource family. |
| `gts.x.core.events.event.*` | Reject | Valid syntax, but selects a different family. |
| `gts.x.core.resources.resource.v1*` | Reject | Invalid wildcard boundary. |

The concrete Type ID `gts.x.core.resources.resource.v1~` is itself a valid pattern: it selects the type, its derived types, and their instances without a trailing `*`. The wildcard in `gts.x.core.resources.resource.*` replaces the version, so it also selects other major versions, such as `gts.x.core.resources.resource.v2~`, and their descendants.

When evaluating access, the application matches the target resource's GTS identifier against `resource_pattern` and evaluates the action under its policy rules (§3.6). Schema validation checks the pattern's syntax and coverage; the policy engine decides whether access is granted.

The option examples are alternatives, not keywords to combine; Options 2 and 3 illustrate proposals that were not chosen.

### Option 1 — Regex in each consumer

Each consumer schema copies the GTS pattern grammar, and any family scope, into a standard `pattern`.

The first regex below copies the identifier and wildcard syntax; the second restricts it to the resource family. Length and whitespace checks are also consumer-owned:

```json
{
  "type": "string",
  "maxLength": 1024,
  "not": { "pattern": "\\s" },
  "allOf": [
    {
      "pattern": "^gts\\.(?:(?:(?:[a-z_][a-z0-9_]*\\.){4}v(?:0|[1-9][0-9]*)(?:\\.(?:0|[1-9][0-9]*))?~)+(?:(?:[a-z_][a-z0-9_]*\\.){4}v(?:0|[1-9][0-9]*)(?:\\.(?:0|[1-9][0-9]*))?|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?|(?:(?:[a-z_][a-z0-9_]*\\.){4}v(?:0|[1-9][0-9]*)(?:\\.(?:0|[1-9][0-9]*))?~)*(?:[a-z_][a-z0-9_]*\\.(?:[a-z_][a-z0-9_]*\\.(?:[a-z_][a-z0-9_]*\\.(?:[a-z_][a-z0-9_]*\\.(?:v(?:(?:0|[1-9][0-9]*)\\.)?)?)?)?)?)?\\*)$"
    },
    {
      "pattern": "^gts\\.x\\.core\\.resources\\.resource\\."
    }
  ]
}
```

This accepts the wildcard for the whole resource family, the concrete resource Type ID, the narrower bucket pattern, and the exact bucket identifier above. Each consumer must maintain the copied grammar and family boundaries as GTS evolves.

### Option 2 — Reuse or relax `x-gts-ref`

Use `x-gts-ref` for pattern-valued fields, or relax it so that its value may be a pattern.

```json
{
  "type": "string",
  "x-gts-ref": "gts.x.core.resources.resource.*"
}
```

Under current semantics this rejects the example payload: the field value must be a concrete identifier, even though the keyword operand may be a pattern. Accepting the bucket wildcard in `resource_pattern` would require changing `x-gts-ref` to validate pattern values and their coverage, and revisiting what registry lookup means for those values. The exact bucket identifier already meets the concrete-value requirement.

### Option 3 — Format with consumer constraints

A `format: "gts-id-pattern"` checks pattern syntax; consumers add short `pattern`s for kind and family.

```json
{
  "type": "string",
  "format": "gts-id-pattern",
  "pattern": "^gts\\.x\\.core\\.resources\\.resource\\."
}
```

The format checks the complete value's syntax. The consumer regex limits it to the resource family across all versions, ending at the token boundary after `resource`. A scope restricted to a particular major version would need a more specific regex that also encodes the version boundaries.

### Option 4 — One keyword for syntax and coverage

A keyword checks the syntax of its operand and value and requires the operand's scope to cover the value; the operand `gts.*` checks syntax only. It is named `x-gts-pattern-ref`, paralleling `x-gts-ref`; `x-gts-pattern` was considered as an alternative name.

```json
{
  "type": "string",
  "x-gts-pattern-ref": "gts.x.core.resources.resource.*"
}
```

The keyword checks both pattern syntax and that every identifier selected by the field value belongs to this resource family. Using `"x-gts-pattern-ref": "gts.*"` instead would accept any valid GTS identifier pattern without a family restriction.

## Decision Outcome

Chosen option: "Option 4", because one keyword handles both syntax-only and family-scoped fields. A separate format is not introduced because `"x-gts-pattern-ref": "gts.*"` already provides the syntax-only check.

### Semantics

- **Operands.** The operand is a concrete GTS Type ID, a concrete GTS Instance ID, a wildcard pattern (§10), or exactly `/$id`. Other pointer forms and invalid operands are schema errors.
- **Effective self-reference.** `/$id` resolves to the canonical top-level `$id` of the effective leaf GTS Type Schema selected for validation, without `gts://`. That root is retained through inherited constraints, `$ref`, and `allOf`, as for `x-gts-ref` (§9.6.1); it is not the `$id` of the subschema containing the keyword. A missing or invalid selected identifier is a schema error.
- **Validity.** A string value must be a valid GTS identifier pattern and satisfy M(value) ⊆ M(operand), after resolving `/$id`. M(p) contains all canonical GTS identifiers selected by p under the literal and wildcard matching rules of §9.6.1 and §10, regardless of registration.
- **Matching.** A concrete Type ID selects itself and its descendants (`root~` ≡ `root~*`), with minor-version flexibility. A concrete Instance ID selects only that exact identifier, with no minor-version expansion. Wildcards follow §10: first-segment `v1.*` and `v1~*` are equivalent; in later segments, `v1.*` also selects instances.
- **Spelling.** The GTS grammar governs spelling and length: no trimming, case folding, or `gts://` stripping from field values; at most 1024 characters; no numeric limits beyond §2.3.
- **Applicability and errors.** Use the same property-value applicability, schema locations, traversal, and validation paths as `x-gts-ref` (§9.6.1), including array-item schemas and effective trait-schema properties. The keyword constrains strings only; schemas specify `"type": "string"` separately. Literal data is not scanned. An invalid or uncovered value is a validation error that `not` can invert; an invalid operand is a schema error and cannot be inverted.
- **No registry lookup.** `gts-ref-validation`, the §9.2 dependency closure, and OP#7 reference tracking do not apply.

Property schema accepting any valid pattern:

```json
{ "type": "string", "x-gts-pattern-ref": "gts.*" }
```

Property schema for patterns within the resource family:

```json
{ "type": "string", "x-gts-pattern-ref": "gts.x.core.resources.resource.*" }
```

A property whose pattern is scoped to the selected type:

```json
{
  "$id": "gts://gts.x.core.resources.resource.v1~",
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

## More Information

[README §9.6.1](../README.md#961-entity-references-x-gts-ref) defines literal matching and selected-type self-reference; [README §10](../README.md#10-collecting-identifiers-with-wildcards) defines wildcards. [Issue #96](https://github.com/GlobalTypeSystem/gts-spec/issues/96) concerns the kind of concrete references; this keyword accepts pattern-valued properties and does not require an additional `pattern` constraint.
