# ADR-0008: Entity reference kinds — `x-gts-type-ref` and `x-gts-instance-ref`

- **Status:** Accepted <!-- Accepted on merge, per CONTRIBUTING.md. -->
- **Date:** 2026-10-13
- **Deciders:** GTS spec maintainers
- **Consulted:** aviator5
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

The former `x-gts-ref` keyword selected a family of GTS identifiers without distinguishing references to types from references to instances. A string can satisfy the declared reference constraint while violating the meaning of its field.

Throughout this ADR, the **operand** is the value assigned to a reference keyword in the schema; the **candidate** is the field value being validated in the data. For example:

```json
{
  "type": "string",
  "x-gts-instance-ref": "gts.x.core.events.topic.v1~"
}
```

The operand is the Type ID `gts.x.core.events.topic.v1~`. If the field contains `gts.x.core.events.topic.v1~x.commerce.orders.orders.v1`, that Instance ID is the candidate. The keyword constrains the candidate's kind; an instance-reference operand can be a Type ID defining the allowed family.

For example, a VM's `powerState` refers to a state instance, such as `running`. Constraining it with `"x-gts-ref": "gts.x.infra.compute.vm_state.v1~"` also accepts the state Type ID itself and derived Type IDs. The same problem affects module capability references and event `topicRef` traits. Conversely, a field intended to identify a type can accept an instance under that type.

Wildcard matching cannot express the missing distinction: a chain wildcard includes the type root and descendants of both kinds. Registry presence does not solve it either, because both types and instances can be registered.

How should schemas express the kind of an entity reference?

This decision adds kind constraints and removes the ambiguous keyword from the supported vocabulary. It reuses the selected-leaf `/$id` semantics settled in [issue #109](https://github.com/GlobalTypeSystem/gts-spec/issues/109) and the matching rules of §10. Pattern-valued fields remain covered by [ADR-0007](0007-gts-pattern-ref.md).

## Decision Drivers

- Make the intended kind visible in the property schema and enforce it in every GTS implementation.
- Retain one definition of identifier syntax, rooted matching, wildcard boundaries, and minor-version matching.
- Support both literal operands and selected-type self-reference for both kinds.
- Detect invalid operands as schema errors, independently of which payload branch is evaluated.
- Make the required kind explicit in every supported entity-reference declaration.
- Preserve JSON Schema composition and separate structural reference checks from optional registry lookup.

## Considered Options

- Option 1 — Keep `x-gts-ref` and add consumer regexes
- Option 2 — Add a companion kind keyword
- Option 3 — Extend `x-gts-ref` with an object operand
- Option 4 — Add two keywords and retain the legacy keyword with warnings
- Option 5 — Add two keywords and reject the legacy keyword *(chosen)*

Options 4 and 5 use the same keyword design and differ only in legacy support: continued legacy support with warnings versus removal from the supported GTS keyword set.

The examples below use an illustrative event subscription. It specifies which event type to receive and which topic instance to receive events from:

```json
{
  "$id": "gts://gts.x.core.events.subscription.v1~",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "eventType",
    "topicRef"
  ],
  "properties": {
    "eventType": {
      "type": "string"
    },
    "topicRef": {
      "type": "string"
    }
  }
}
```

`eventType` selects an event type, such as `order_placed`, including its derived event types. `topicRef` identifies a particular topic, such as `orders`. These fields refer to different entities: the type encoded in the topic ID describes the topic itself, not the events the subscriber wants to receive. An intended payload is:

```json
{
  "eventType": "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1~",
  "topicRef": "gts.x.core.events.topic.v1~x.commerce.orders.orders.v1"
}
```

Each option supplies a replacement for `properties`. These are alternative designs, not keywords to combine; Options 2 and 3 illustrate vocabulary that this decision does not introduce.

### Option 1 — Keep `x-gts-ref` and add consumer regexes

Retain the existing reference constraint and use JSON Schema `pattern` to restrict the final character of a valid identifier.

```json
{
  "eventType": {
    "type": "string",
    "x-gts-ref": "gts.x.core.events.type.v1~",
    "pattern": "~$"
  },
  "topicRef": {
    "type": "string",
    "x-gts-ref": "gts.x.core.events.topic.v1~",
    "not": {
      "pattern": "~$"
    }
  }
}
```

`x-gts-ref` checks the complete identifier syntax and family; the regex distinguishes the kind by the final `~`.

### Option 2 — Add a companion kind keyword

Keep the reference scope in `x-gts-ref` and introduce `x-gts-ref-kind`.

```json
{
  "eventType": {
    "type": "string",
    "x-gts-ref": "gts.x.core.events.type.v1~",
    "x-gts-ref-kind": "type"
  },
  "topicRef": {
    "type": "string",
    "x-gts-ref": "gts.x.core.events.topic.v1~",
    "x-gts-ref-kind": "instance"
  }
}
```

### Option 3 — Extend `x-gts-ref` with an object operand

Put the kind and reference scope into one operand.

```json
{
  "eventType": {
    "type": "string",
    "x-gts-ref": {
      "kind": "type",
      "target": "gts.x.core.events.type.v1~"
    }
  },
  "topicRef": {
    "type": "string",
    "x-gts-ref": {
      "kind": "instance",
      "target": "gts.x.core.events.topic.v1~"
    }
  }
}
```

### Option 4 — Add two keywords and retain the legacy keyword with warnings

New schemas use explicit kinds, while an old declaration remains valid and produces a warning:

```json
{
  "eventType": {
    "type": "string",
    "x-gts-type-ref": "gts.x.core.events.type.v1~"
  },
  "topicRef": {
    "type": "string",
    "x-gts-instance-ref": "gts.x.core.events.topic.v1~"
  },
  "legacyTopicRef": {
    "type": "string",
    "x-gts-ref": "gts.x.core.events.topic.v1~"
  }
}
```

`topicRef` rejects a Type ID; `legacyTopicRef` still accepts one and emits a deprecation warning for the keyword.

### Option 5 — Add two keywords and reject the legacy keyword

Use one keyword per reference kind:

```json
{
  "eventType": {
    "type": "string",
    "x-gts-type-ref": "gts.x.core.events.type.v1~"
  },
  "topicRef": {
    "type": "string",
    "x-gts-instance-ref": "gts.x.core.events.topic.v1~"
  }
}
```

The legacy `x-gts-ref` keyword leaves the supported GTS keyword set. The `legacyTopicRef` declaration from Option 4 is consequently handled as an unknown `x-gts-*` keyword under the ordinary validation rules.

## Decision Outcome

Chosen option: "Option 5". Two keywords make the intended kind part of each reference declaration. Removing the old keyword requires authors to review ambiguous references before their schemas can pass validation under the new contract; warnings would continue to admit those schemas with the original defect. This is a breaking change using the existing unknown-GTS-keyword validation path.

### Operands and schema errors

Both keywords take a single string operand. They reuse §10 syntax and matching, with one additional restriction: **`x-gts-type-ref` MUST reject a concrete Instance ID operand**, including a UUID-tailed Instance ID. Such an operand selects only instances and cannot satisfy a type reference. Here, “Instance ID” describes identifier syntax; it has no connection to the `x-gts-final` modifier.

| Operand | `x-gts-type-ref` | `x-gts-instance-ref` |
|---|---|---|
| Concrete Type ID, e.g. `gts.x.infra.compute.vm_state.v1~` | Allowed: selects matching types. | Allowed: selects instances rooted at matching types. |
| Concrete Instance ID, e.g. `gts.x.infra.compute.vm_state.v1~x.infra._.running.v1` | Schema error. | Allowed: selects matching instances under §10 minor-version rules. |
| Valid wildcard, e.g. `gts.*` or `gts.x.infra.compute.vm_state.v1~*` | Allowed: candidate must be a type. | Allowed: candidate must be an instance. |
| Exactly `/$id` | Allowed: resolve to the selected leaf Type ID. | Allowed: resolve to the same selected leaf Type ID. |
| Other slash-prefixed strings, including `/properties/type`, `/gts.x.infra.compute.vm_state.v1~`, and `/$id/` | Schema error. | Schema error. |
| Empty string, malformed ID/pattern, `gts://` URI, non-string value | Schema error. | Schema error. |

Operand syntax checks include §2/§10 spelling, the 1024-character limit, unsigned 32-bit version components, and wildcard placement. No trimming, case folding, or automatic conversion from a `gts://` URI is performed. The keyword name constrains the **candidate**, so a wildcard is not required to end in `~`. For example, `gts.x.infra.compute.vm_state.v1.*` is valid for either keyword; its explicit-minor requirement remains in force.

Both keywords follow the same validation lifecycle as `x-gts-pattern-ref` ([§9.6.2](../README.md#962-pattern-valued-fields-x-gts-pattern-ref)): operands MUST be checked during registration with validation enabled, explicit schema validation, and before instance or trait value validation, even if registration skipped validation. Registration with `validate=false` may defer these checks; storing a schema does not establish its validity. As with `x-gts-pattern-ref`, early rejection is also permitted: `validate=false` does not require accepting an invalid schema.

When these checks run, an invalid operand is a schema error even if its property is absent or its subschema is in an unselected `anyOf`, `if`, or `not` branch. A schema error cannot be inverted by `not` or rescued by another successful branch. Follow [§9.6.3](../README.md#963-common-validation-rules)'s dialect-aware traversal of schema locations, including array-item schemas and effective trait schemas; do not scan literal data for keyword names.

### Candidate validation and selected-type self-reference

Let `M(p)` be the set selected by operand `p` under §10, after resolving `/$id`. Let `T` and `I` be the sets of syntactically valid canonical Type and Instance IDs. A string candidate `v` satisfies the structural reference constraint exactly when:

- `x-gts-type-ref`: `v ∈ M(p) ∩ T`;
- `x-gts-instance-ref`: `v ∈ M(p) ∩ I`.

Parse the complete identifier before determining its kind: Type IDs end in `~`; Instance IDs do not. A suffix check alone cannot establish validity. Field values MUST be concrete identifiers, never wildcards, pointers, or `gts://` URIs, and MUST obey the same spelling and length rules as other canonical identifiers.

Both keywords constrain strings only, consistently with `x-gts-pattern-ref`. Use `"type": "string"` separately to reject other JSON values. They do not imply `required`; optional absent properties remain optional. A malformed candidate, wrong kind, or mismatch is a value-validation failure subject to ordinary JSON Schema composition.

For the operand `gts.x.infra.compute.vm_state.v1~`:

| Candidate | Type reference | Instance reference |
|---|:---:|:---:|
| `gts.x.infra.compute.vm_state.v1~` | Accept | Reject |
| `gts.x.infra.compute.vm_state.v1~acme.infra._.extended_state.v1~` | Accept | Reject |
| `gts.x.infra.compute.vm_state.v1~x.infra._.running.v1` | Reject | Accept |
| `gts.x.infra.compute.vm_state.v1~acme.infra._.extended_state.v1~acme.infra._.running.v1` | Reject | Accept |
| `gts.x.infra.compute.vm_state.v1~7a1d2f34-5678-49ab-9012-abcdef123456` | Reject | Accept |
| `gts.x.infra.compute.vm_state.v2~` | Reject | Reject |
| `gts.x.infra.compute.vm_state.v1~*` | Reject | Reject |

These are structural results, before registry policy. Matching uses parsed chain boundaries and existing minor-version rules, never raw lexical `startsWith`.

`/$id` is supported by **both** keywords and resolves to the canonical top-level identifier of the leaf GTS Type Schema selected for validation, with `gts://` removed. It retains that root through inherited or composed constraints. A missing or invalid selected Type ID is a schema error under the same operand-checking rules, including absent properties and unselected branches. It is a reserved operand, not general JSON Pointer support.

For a field referencing the selected type or a derived type, use this property schema:

```json
{ "type": "string", "x-gts-type-ref": "/$id" }
```

For a field referencing an instance under the selected type, use this property schema instead:

```json
{ "type": "string", "x-gts-instance-ref": "/$id" }
```

Suppose either constraint is declared in `gts.x.infra.compute.vm.v1~`, and a derived `gts.x.infra.compute.vm.v1~acme.infra._.special_vm.v1~` schema explicitly imports it through `$ref`. In either case, the operand resolves to that derived Type ID. The type-reference constraint accepts that type and matching further-derived types; the instance-reference constraint accepts instances under them. Both reject ancestor and sibling references. A chained `$id` alone does not import the base schema body. Use a literal operand to retain a fixed base root, or `const` to require exact identifier spelling.

### Composition and additional restrictions

To accept either kind explicitly:

```json
{
  "type": "string",
  "anyOf": [
    { "x-gts-type-ref": "gts.x.infra.compute.vm_state.v1~" },
    { "x-gts-instance-ref": "gts.x.infra.compute.vm_state.v1~" }
  ]
}
```

Declaring both keywords in the same schema object means conjunction, as does combining them through `allOf`. No string satisfies both kinds. This is not a new schema error: JSON Schema permits unsatisfiable constraints, including deliberately false branches. Implementations MAY lint this combination. The same distinction applies to a conflicting `const`, `enum`, or `pattern`; no general satisfiability checker is required at registration.

Use standard keywords for additional restrictions. For example, this permits exactly one Type ID, excluding derived types and alternate minor spellings:

```json
{
  "type": "string",
  "x-gts-type-ref": "gts.x.infra.compute.vm_state.v1~",
  "const": "gts.x.infra.compute.vm_state.v1~"
}
```

A concrete Instance ID operand also retains omitted-minor flexibility. Add `const` when exact spelling is required; do not silently reinterpret the operand as equality.

No new ban on references to abstract or final types is introduced. A type reference may identify either. An instance-reference operand may be an abstract base with concrete descendants, or a final type with direct instances. Existing target-validity rules determine whether a referenced entity illegally instantiates an abstract type or derives from a final type; these facts are not inferable from the identifier alone.

### Registry policy and enforcement

Structural checks, including candidate kind, are mandatory regardless of registry lookup policy. `gts-ref-validation=none` skips lookup, not syntax, matching, or kind validation. The existing optional `any-present` and `any-valid` policies apply to both new keywords.

For the subscription's `topicRef` in Option 5, suppose the supplied candidate is `gts.x.core.events.topic.v1~x.commerce.orders.orders.v1`. Under `any-present`, lookup performs two independent checks:

| Reference component | Required registry entry |
|---|---|
| Operand: `gts.x.core.events.topic.v1~` | The topic **type**, by its exact identifier. |
| Candidate: `gts.x.core.events.topic.v1~x.commerce.orders.orders.v1` | The orders topic **instance**, by its exact identifier. |

The candidate must also pass syntax, family matching, and instance-kind checks. Under `any-valid`, both referenced entities must additionally be valid under the existing transitive validation rule.

If the operand is instead `gts.x.core.events.topic.v1~*`, the existing wildcard rule requires at least one matching registered entity (`any-present`) or valid registered entity (`any-valid`), regardless of kind. The registered topic type can satisfy this operand check. It does not satisfy lookup for a supplied instance candidate: if the orders topic instance is missing, that candidate still fails. The instance-kind restriction applies to the candidate, not to the entity establishing the wildcard operand's presence.

The new keywords apply on the existing entity and trait validation paths, including materialized effective trait values inherited from ancestors or supplied by defaults. Abstract types do not skip reference validation. No new registry dependency behavior is introduced beyond the chosen reference policy.

### Supported vocabulary

`x-gts-ref` is removed from the supported GTS keyword set. Implementations handle it exactly like any unknown `x-gts-*` keyword, under the ordinary validation lifecycle: registration with validation enabled, explicit schema validation, and validation of data against the schema reject it. Registration with `validate=false` may defer this check or reject early. No separate compatibility mode or alias is introduced.

### Derivation, evolution, and casting

For both keywords, compatibility compares the kind-filtered scopes defined above. OP#12 requires `Valid(derived) ⊆ Valid(base)`; OP#8 uses the backward, forward, and full relations of §4.3. For isolated positive constraints with registry lookup disabled, narrowing is permitted by derivation and is forward compatible for evolution; widening is backward compatible; equal scopes are fully compatible. Switching between nonempty type and instance scopes satisfies neither inclusion direction.

Complete schemas must be assessed as a whole, accounting for composition, registry policy, and the selected-leaf root for `/$id` in each context. OP#8 reports `unknown` when compatibility cannot be established. Optional OP#9 identity-field rewriting is reported separately from schema compatibility.

### Implications

- Update README §9.6.1 and related operations, trait rules, keyword-placement descriptions, and examples to describe the new keywords and rejection of the old one. Keep historical ADRs intact.
- Add a BREAKING document-version entry for specification version 0.17 and preserve historical release entries.
- Update JSON Schema, YAML, and TypeSpec examples by field intent, including identity fields, traits, and array items.
- Conformance cases must cover valid and invalid operands, the Type-ID/Instance-ID operand asymmetry, well-known and UUID-tailed candidates, wrong-kind rejection, direct and derived candidates, wildcard/minor-version behavior, and exact `const` restrictions.
- Reuse #109's selected-leaf cases for both keywords: direct declaration, inline `allOf`, external `$ref`, further derivation, ancestor/sibling rejection, and absence of implicit inheritance from a chained ID.
- Cover `anyOf`, `allOf`, `not`, non-string applicability, optional absent properties, and invalid operands in unselected branches. Verify that legacy-keyword handling matches unknown `x-gts-*` handling for registration with and without validation and for subsequent explicit validation, while identically named literal data and property names remain allowed.
- Cover every supported dialect and registry mode, including operand lookup versus candidate kind, effective traits, abstract/final targets, and OP#8/OP#9 reporting. Negative candidate tests should use otherwise-valid schemas and available targets to isolate kind rejection from unrelated failures.
- After merging the ADR and conformance contract, track implementation updates in the reference implementation repositories, including `gts-go` and `gts-rust` as requested in #96. This ADR alone does not change their behavior.

## Pros and Cons of the Options

### Option 1 — Keep `x-gts-ref` and add consumer regexes

- **+** No new GTS vocabulary; existing validators can enforce the combination.
- **−** Every author must remember the suffix restriction; omitting it silently permits both kinds. Tools must recognize the combination to infer reference kind.

### Option 2 — Add a companion kind keyword

- **+** Keeps kind and family as explicit, independent dimensions.
- **−** Requires rules for standalone and independently composed companions. Making the companion optional preserves the defect; requiring it is still a breaking change.

### Option 3 — Extend `x-gts-ref` with an object operand

- **+** Groups the reference settings and leaves room for future options.
- **−** Adds an operand grammar and verbosity without a current need; retaining strings leaves ambiguity, while removing strings still breaks compatibility.

### Option 4 — Add two keywords and retain the legacy keyword with warnings

- **+** Keeps existing schemas working while warning about ambiguous references.
- **−** Keeps kind-blind validation indefinitely unless a later breaking removal is enforced; requires consistent warning delivery.

### Option 5 — Add two keywords and reject the legacy keyword

- **+** Simple, explicit declarations; the ambiguous keyword leaves the supported vocabulary.
- **+** Reuses existing matching and self-reference rules and expresses mixed-kind fields through standard composition.
- **−** Breaks every schema using the old keyword and requires coordinated schema and implementation updates.

## More Information

- [Issue #96: Split `x-gts-ref`](https://github.com/GlobalTypeSystem/gts-spec/issues/96).
- [Issue #109: Selected-leaf `/$id` resolution](https://github.com/GlobalTypeSystem/gts-spec/issues/109).
- [README §9.6.1](../README.md#961-entity-references-x-gts-type-ref--x-gts-instance-ref): current entity-reference rules, schema locations, and registry policies.
- [README §10](../README.md#10-identifier-matching-and-pattern-coverage): shared selection and minor-version rules.
- [ADR-0007](0007-gts-pattern-ref.md): pattern-valued fields, distinct from concrete entity references.
- [Unknown GTS extension conformance cases](../tests/test_op6_schema_validation.py): existing coverage rejects unknown `x-gts-*` keywords at registration with validation enabled. The specification update should state this shared vocabulary-validation rule explicitly alongside the supported keyword set.
- Target specification version: 0.17.
