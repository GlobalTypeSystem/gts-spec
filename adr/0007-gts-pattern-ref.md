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
- Identifier-selection rules shared with `x-gts-ref`; pattern values additionally require coverage.

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

The scope's schema should allow patterns within the resource family, including instance selectors with flexible or pinned minor versions:

| `resource_pattern` value | Result | Resource selection |
|---|---|---|
| `gts.x.core.resources.resource.*` | Accept | All versions of the resource type and all derived types and instances. |
| `gts.x.core.resources.resource.v1~` | Accept | This resource type and all derived types and instances, with minor-version flexibility within major version 1. |
| `gts.x.core.resources.resource.v1~acme.storage.resources.bucket.*` | Accept | All versions of the bucket type and all derived types and instances under resource major version 1. |
| `gts.x.core.resources.resource.v1~acme.storage.resources.bucket.v1~acme.prod._.uploads.v1` | Accept | Bucket instances with these segment names and major versions, across minor versions. |
| `gts.x.core.resources.resource.v1.0~acme.storage.resources.bucket.v1.0~acme.prod._.uploads.v1.0` | Accept | Exactly one bucket instance; every minor is explicit. |
| `gts.x.core.resources.*` | Reject | Valid syntax, but a broader scope that can select identifiers outside the resource family. |
| `gts.x.core.events.event.*` | Reject | Valid syntax, but selects a different family. |
| `gts.x.core.resources.resource.v1*` | Reject | Invalid wildcard boundary. |

The concrete Type ID `gts.x.core.resources.resource.v1~` is itself a valid pattern: it selects the type, its derived types, and their instances without a trailing `*`. The wildcard in `gts.x.core.resources.resource.*` replaces the version, so it also selects other major versions, such as `gts.x.core.resources.resource.v2~`, and their descendants.

When evaluating access, the application matches the target resource's GTS identifier against `resource_pattern` and evaluates the action under its policy rules (§3.6). Schema validation checks the pattern's syntax and coverage; the policy engine decides whether access is granted.

The option examples are alternatives, not keywords to combine; Options 2 and 3 illustrate proposals that were not chosen.

### Option 1 — Regex in each consumer

Each consumer schema copies the GTS pattern grammar, and any family scope, into a standard `pattern`.

The first regex below recognizes identifier and wildcard structure; the second restricts it to the resource family. The example includes length and whitespace checks, but consumers must additionally enforce the unsigned 32-bit version bounds in §2.3:

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

This accepts the wildcard for the whole resource family, the concrete resource Type ID, the narrower bucket pattern, and the bucket instance selectors above. Each consumer must maintain the copied grammar and family boundaries as GTS evolves.

### Option 2 — Reuse or relax `x-gts-ref`

Use `x-gts-ref` for pattern-valued fields, or relax it so that its value may be a pattern.

```json
{
  "type": "string",
  "x-gts-ref": "gts.x.core.resources.resource.*"
}
```

Under current semantics this rejects the example payload: the field value must be a concrete identifier, even though the keyword operand may be a pattern. Accepting the bucket wildcard in `resource_pattern` would require changing `x-gts-ref` to validate pattern values and their coverage, and revisiting what registry lookup means for those values. Both bucket instance selectors already meet the concrete-value requirement.

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
- **Validity.** A string value must be a valid GTS identifier pattern and satisfy M(value) ⊆ M(operand), after resolving `/$id`. M(p) contains all canonical GTS identifiers selected by p under [README §10](../README.md#10-identifier-matching-and-pattern-coverage), including its minor-version rules, regardless of registration.
- **Spelling.** The GTS grammar governs spelling and length: no trimming, case folding, or `gts://` stripping from field values; at most 1024 characters; major and minor versions follow the unsigned 32-bit range of §2.3.
- **Applicability and errors.** Use the same property-value applicability, schema locations, traversal, and validation paths as `x-gts-ref` (§9.6.1), including array-item schemas and effective trait-schema properties. The keyword constrains strings only; schemas specify `"type": "string"` separately. Literal data is not scanned. An invalid or uncovered value is a validation error that `not` can invert; an invalid operand is a schema error and cannot be inverted.
- **No registry lookup.** Coverage checks do not query the registry or depend on target registration or validity. `gts-ref-validation` does not apply to this keyword, and the keyword does not introduce validation dependencies under §9.2. OP#7 reporting for its operands and values follows [README §9.6.2](../README.md#962-pattern-valued-fields-x-gts-pattern-ref).

Property schema accepting any valid pattern:

```json
{ "type": "string", "x-gts-pattern-ref": "gts.*" }
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

No separate compatibility model is introduced. Pattern constraints participate in the accepted-instance-set relations of §4.1 and §4.3. [README §9.6.2](../README.md#962-pattern-valued-fields-x-gts-pattern-ref) defines their treatment in OP#12 and OP#8, including composition and selected-type self-reference.

### Implications

- README §9 defines the keyword, and §10 adds coverage to the pattern grammar. The specification and conformance suite implement this decision for 0.16.
- Conformance coverage and its limits are documented in [tests/README.md](../tests/README.md#gts-identifier-pattern-constraint-tests).
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

[README §9.6.1](../README.md#961-entity-references-x-gts-ref) defines entity references and selected-type self-reference; [README §10](../README.md#10-identifier-matching-and-pattern-coverage) defines matching and coverage. [Issue #96](https://github.com/GlobalTypeSystem/gts-spec/issues/96) concerns the kind of concrete references; this keyword accepts pattern-valued properties and does not require an additional `pattern` constraint.
