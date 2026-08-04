# ADR-0001: Expressing derivation in GTS Type Schemas — GTS as a JSON Schema Extension (dialect-agnostic)

- **Status:** Accepted
- **Date:** 2026-05-27
- **Deciders:** GTS spec maintainers
- **Consulted:** —
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

GTS expresses type derivation through **chained `$id`s**: `gts://A~` is a base type, `gts://A~B~` is a derived type whose immediate parent is `gts://A~`. The chain establishes the *fact* of derivation; operation **OP#12 ("Type Derivation Validation")** enforces the *semantic compatibility* contract — every valid instance of the derived schema must also be a valid instance of every ancestor in its chain.

What the spec has so far been silent about is the structural side: **how should the JSON Schema document of a derived type be written?**

### JSON Schema has no derivation concept

This is the central observation. JSON Schema (Draft-07 and beyond) offers **composition** keywords — [`allOf`](https://json-schema.org/understanding-json-schema/reference/combining#allof), `oneOf`, `anyOf`, `not` — but **none** of them mean "parent type." `allOf` in particular is defined as a logical **AND** over [subschemas](https://json-schema.org/learn/glossary#subschema) at instance-validation time, nothing more:

- It does not designate a "base."
- It carries no inheritance semantics.
- It imposes no "first item must be the parent" rule.
- It is symmetric: `allOf: [A, B]` and `allOf: [B, A]` produce the same effective constraints.

Implementations and authors that today use `allOf` with a `$ref` to a parent type to express derivation are using `allOf` **by convention**, not by language design.

### What the spec has not said

Given the above, an author writing a derived `gts://A~B~` schema has no normative guidance on:

- Whether they MUST use `allOf` with a `$ref` to the parent, or MAY skip `allOf` entirely and re-declare the parent's fields in the derived schema body.
- Where to place `properties` / `required` / `additionalProperties` / `x-gts-*` modifiers.
- Whether shapes like multi-item `allOf`, hybrid overlays (top-level overlay AND another inside `allOf`), or top-level `oneOf` / `anyOf` are admissible.

In practice every reference implementation and every example under `examples/**/types/` happens to use the same convention — a 2-item `allOf` with a `$ref` to the parent plus an inline overlay — but this is convention, not contract.

### Why this matters

- **Authoring friction.** Newcomers ask "do I have to use `allOf`? where do I put `properties`?" and get no answer from the spec.
- **Cross-implementation variance.** Implementations may diverge on which shapes they accept (for example, a derived schema that lists parent fields directly without `allOf`).
- **Tooling assumptions.** Codegen, linters, and structural diffs assume a particular shape because there is nothing else to assume from.
- **`additionalProperties` interaction with `$ref`.** This is a well-known Draft-07 footgun and one of the reasons authoring guidance feels urgent. This ADR **acknowledges** the footgun but explicitly defers it to a separate discussion.

### The framing this ADR adopts

GTS positions itself as an **extension of JSON Schema**, dialect-agnostic. It **extends** JSON Schema with vendor keywords (`x-gts-traits-schema`, `x-gts-traits`, `x-gts-final`, `x-gts-abstract`, `x-gts-ref`, …) and **adds** registry-enforced semantic rules (derivation compatibility, finality, abstractness, traits). The dialect of any concrete GTS Type Schema is determined by its `$schema`; the spec's examples use Draft-07 as the baseline for maximum interoperability, but Draft 2019-09 and Draft 2020-12 are equally acceptable provided the dialect's keywords are used consistently. GTS does **not** forbid syntactically valid JSON Schema constructs from any of these dialects, and in particular it does **not** require `allOf` for derivation.

This ADR does **not** make GTS a [JSON Schema Dialect](https://json-schema.org/learn/glossary#dialect) in the formal sense: GTS does not publish a dedicated `$schema` URI or meta-schema (each GTS Type Schema declares its dialect via the standard `$schema` URI of its choice — e.g. `http://json-schema.org/draft-07/schema#`, or a Draft 2019-09 / 2020-12 URI), and all GTS-specific constraints (`$id` shape, `x-gts-*` keyword shapes, derivation compatibility, completeness, etc.) are enforced at the registry rather than by a meta-schema. For the rest of this ADR the term *extension framing* is used. (Whether GTS will eventually become a formal Dialect is an open question — see §11.0 — and this ADR does not depend on either outcome.)

## Decision Drivers

- **Faithfulness to JSON Schema.** A user's existing JSON Schema, if it carries a valid GTS `$id` and `$schema`, should "just work" as a GTS Type Schema syntactically.
- **Derivation is GTS-level, not JSON-Schema-level.** Lineage lives in the `$id`. The schema body can express compatibility however its author chooses.
- **Author flexibility.** `allOf` is a convenient tool, not a mandate.
- **Separation of syntactic vs semantic validity.** Semantic compatibility (OP#12) is the contract that matters; syntax is incidental.

## Considered Options

- Option 1 — Strict canonical form
- Option 2 — GTS Type Schema as a JSON Schema Extension (dialect-agnostic) *(chosen)*

Both options use the same running example.

### Running example used in this section

The base type `gts.x.example.user.v1~` is registered once and is identical across options:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~",
  "type": "object",
  "required": ["id", "name"],
  "properties": {
    "id":   { "type": "string" },
    "name": { "type": "string" }
  }
}
```

The derived type we want to register is `gts.x.example.user.v1~vendor.premium_user.v1~` — a `premium_user` that extends `user` by adding a required `tier` field constrained to the enum `["gold", "platinum"]`. The concrete derived schema is shown under each option below, because the question of *what shapes are admissible* is exactly what the two options disagree on.

Two instance payloads are referenced throughout:

```json
// P-OK
{ "id": "u-1", "name": "Alice", "tier": "gold" }
```

```json
// P-BAD — has no `tier`
{ "id": "u-2", "name": "Bob" }
```

### Option 1 — Strict canonical form

The spec mandates exactly one shape for derived schemas: `allOf` with the first (and possibly only) item being a `$ref` to the immediate parent, with `type`, `properties`, `required`, modifiers, and trait keywords placed at the **top level** of the derived schema. All other shapes are rejected at registration.

*The single admissible form for `premium_user` under this option:*

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": {
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  }
}
```

P-OK validates; P-BAD fails (no `tier`).

*An equivalent description that does NOT use `allOf` — parent fields listed directly:*

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "required": ["id", "name", "tier"],
  "properties": {
    "id":   { "type": "string" },
    "name": { "type": "string" },
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  }
}
```

Effectively equivalent — every instance valid against this schema is valid against the parent and vice versa where the parent's fields are concerned. **Under Option 1, this form is rejected at registration** because the spec requires `allOf` + `$ref` to the parent. Authors who would naturally write a derived schema this way must rewrite it to use `allOf`, even though no semantic content changes.

**Pros:** one shape for tools to recognise; a single inspection path for validators, linters, and codegen.

**Cons:** conflicts with the extension framing — the spec ends up defining a *subset* of JSON Schema rather than a superset; outlaws otherwise-valid JSON Schemas; rejects derived schemas that simply choose not to use `allOf`; migrates / invalidates third-party schemas that happen to use a different shape; introduces a structural validator branch that every implementation must keep in sync.

### Option 2 — GTS Type Schema as a JSON Schema Extension (dialect-agnostic) *(CHOSEN)*

GTS does **not** restrict the syntactic form of a derived Type Schema. Any syntactically valid JSON Schema that carries a valid GTS `$id` and a `$schema` URI (Draft-07, Draft 2019-09, Draft 2020-12, or any future dialect that ships GTS support) is **syntactically** a valid GTS Type Schema. `allOf` is **not required** for derivation — derivation is established by the chained `$id`, and compatibility with the ancestor chain is checked semantically by OP#12. What matters is that the derived schema satisfies all **derivation compatibility rules** (described elsewhere in the spec).

GTS still layers in:

- **New keywords** — `x-gts-traits-schema`, `x-gts-traits`, `x-gts-final`, `x-gts-abstract`, `x-gts-ref`, and so on (see README §9.x and §11).
- **Semantic rules** that constrain *meaning*, not syntax — primarily derivation compatibility (OP#12) and the modifiers in §9.11.

**Worked example — the same derived `premium_user~` written three different ways, all valid under Option 2.**

*Variant 2a — `allOf` with `$ref` to parent, overlay at the top level:*

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": {
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  }
}
```

The derived schema delegates the parent's constraints to a `$ref`. Its own body adds `tier`. P-OK validates; P-BAD fails.

*Variant 2b — `allOf` with `$ref` plus inline overlay (the current de-facto convention in examples):*

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "allOf": [
    { "$ref": "gts://gts.x.example.user.v1~" },
    {
      "type": "object",
      "required": ["tier"],
      "properties": {
        "tier": { "type": "string", "enum": ["gold", "platinum"] }
      }
    }
  ]
}
```

Same effective constraints. P-OK validates; P-BAD fails.

*Variant 2c — **no `allOf` at all**; parent fields enumerated directly in the derived schema:*

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "required": ["id", "name", "tier"],
  "properties": {
    "id":   { "type": "string" },
    "name": { "type": "string" },
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  }
}
```

The derived schema restates the parent's fields and adds its own. There is no `$ref` to the parent in the schema body. The lineage is still expressed by the chained `$id`, and OP#12 checks that every valid instance of this derived schema is also a valid instance of `gts.x.example.user.v1~` — which it is, since the derived schema includes `id` and `name` with the same constraints as the parent.

P-OK validates; P-BAD fails. Syntactically valid and semantically compatible — admissible under Option 2.

**Note on `additionalProperties`.** The Draft-07 footgun is acknowledged and explicitly deferred. Under Variant 2c (no `allOf`), `additionalProperties: false` at the top level "sees" all enumerated properties and behaves naturally — one practical reason an author might prefer 2c over 2a/2b. Under 2a/2b the same keyword interacts subtly with `$ref`. This ADR does not solve that.

**Note on conventions.** Implementations and authors MAY still prefer a single shape (e.g., 2b) as a *convention* enforced by linters or by normalization on registration. This ADR does not forbid such conventions; it just refuses to put the restriction in the spec.

## Decision Outcome

Chosen option: **Option 2 — GTS Type Schema as a JSON Schema Extension (dialect-agnostic).**

Key normative consequences:

- A syntactically valid JSON Schema document (in any supported dialect — Draft-07, Draft 2019-09, Draft 2020-12) carrying a valid GTS `$id` and `$schema` IS a syntactically valid GTS Type Schema.
- `allOf` is **not required** to express derivation. Derivation is established by the chained `$id`; compatibility is checked semantically by OP#12.
- Authors MAY choose between `allOf` + `$ref` to parent, `allOf` + inline overlay, no `allOf` at all (parent fields enumerated), or any other syntactically valid composition.
- A schema MAY still be **rejected at registration for semantic reasons** (e.g., violating derivation compatibility), but never purely for shape.

### Implications

- **README §11.0 ("Relationship to JSON Schema")** gains an explicit statement of the extension framing (dialect-agnostic, with Draft-07 as the example baseline) and the non-restriction principle (links to the JSON Schema glossary and to the `allOf` reference).
- **OP#12** scope is unchanged — it remains the semantic compatibility check. README wording that calls `allOf` "recommended" stays as a recommendation, not a requirement.
- **OP#6** is unchanged.
- **Reference implementations (gts-go, gts-rust)** MUST NOT reject derived schemas purely because they omit `allOf`, provided OP#12 semantic compatibility holds.
- **Conformance test suite** carries no "structural rejection" tests. Any existing tests that reject a shape purely because it lacks `allOf` (or uses a different composition) should be removed or rewritten as semantic-compatibility tests.
- **Examples and tests under `examples/**/types/`** are left as-is. The conventional 2-item `allOf` form remains a valid and recommended convention.
- **Backward compatibility:** non-breaking.

## Pros and Cons of the Options

### Option 1 — Strict canonical form

- **+** One shape for tools to recognise; a single inspection path for validators, linters, codegen.
- **−** Conflicts with the extension framing — we'd be defining a *subset* of JSON Schema, not a superset.
- **−** Outlaws otherwise-valid JSON Schemas.
- **−** Rejects no-`allOf` derived schemas that are semantically compatible.
- **−** Invalidates third-party schemas that happen to use a different shape; requires a structural validator branch in every implementation.

### Option 2 — GTS Type Schema as a JSON Schema Extension (dialect-agnostic) (chosen)

- **+** Preserves "every valid JSON Schema is a valid GTS Type Schema," across whichever dialect the author picks.
- **+** Makes the role of `allOf` honest — optional convenience, not a mandate.
- **+** Tooling uniformity, if desired, is addressable by conventions / linters / normalization at the implementation layer.
- **+** Because Option 2 introduces no artificial restrictions and no new concepts beyond the existing JSON Schema vocabulary, the spec needs only one sentence to anchor the entire approach — *"a GTS Type Schema is a JSON Schema document extended with `x-gts-*` keywords and registry-enforced semantic rules"* — and everything else follows from that. **This makes the GTS spec itself simpler**, not just the schemas authored against it.
- **−** Tooling cannot rely on a single canonical inspection path at the spec level; uniformity has to be enforced (if at all) by conventions, linters, or registry-side normalization rather than by the spec.

## More Information

Cross-references inside this specification: README §3.2 (Inheritance), §9.11 (Modifiers), §11.0 (Relationship to JSON Schema), OP#12 (Type Derivation Validation).

External references:

- [`allOf` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/combining#allof)
- [JSON Schema subschema (glossary)](https://json-schema.org/learn/glossary#subschema)
- [JSON Schema Dialect (glossary)](https://json-schema.org/learn/glossary#dialect)
