# ADR-0002: What `x-gts-traits-schema` is — a JSON Schema subschema with chain aggregation

- **Status:** Accepted
- **Date:** 2026-05-27
- **Deciders:** GTS spec maintainers
- **Consulted:** —
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

A GTS host type — an ordinary GTS Type Schema describing instances of some type — may carry **trait metadata**: retention rules, indexing/routing directives, association links, and similar publisher-authored declarations that control system behaviour for instances of the type. Traits live alongside the type definition; they do not appear in instance payloads. Two keywords are used together:

- `x-gts-traits-schema` — declares the **shape** of the trait metadata for this host;
- `x-gts-traits` — carries the concrete **values**.

This ADR is about the **schema side** (`x-gts-traits-schema`). The value side — chain merge of `x-gts-traits` objects, immutability of inherited values, default resolution — is out of scope here.

### The open question

The spec must commit to **what kind of value** `x-gts-traits-schema` is. Two natural framings exist:

- A **URI reference** to a separately-registered GTS Type whose schema describes the trait shape (trait-type as a first-class GTS Type).
- An ordinary [JSON Schema subschema](https://json-schema.org/learn/glossary#subschema) embedded inside the host type.

### Why this matters

Host types form derivation chains (`gts://A~B~`). The descendant's trait-schema must relate somehow to the ancestor's. The choice of value-space drives whether GTS needs a **parallel concept** in the registry — trait-type identity, trait-type derivation chain, trait-type lifecycle and access control — or whether ordinary JSON Schema composition is enough to carry the trait-schema along the host's derivation chain.

### The framing inherited from ADR-0001

ADR-0001 commits GTS to being an **extension of JSON Schema** (dialect-agnostic; not a [JSON Schema Dialect](https://json-schema.org/learn/glossary#dialect) in the formal sense — GTS does not publish a dedicated `$schema` URI or meta-schema): extend JSON Schema with vendor keywords and registry-enforced semantic rules, do not invent parallel registry concepts when JSON Schema mechanisms suffice, and do not impose syntactic restrictions on otherwise-valid JSON Schemas. This ADR continues in that line.

## Decision Drivers

- **Spec simplicity.** Fewer GTS-specific concepts is strictly better, all else equal.
- **Consistency with ADR-0001.** Same extension framing — extend JSON Schema, don't subset or replace it.
- **Authoring ergonomics.** Inline traits, shared traits, and descendant additions should all be cheap to write and read.
- **Compatibility under derivation.** A descendant's effective trait-schema must be a structural narrowing of its ancestor's. This should fall out of the model, not require a separate compatibility rule.
- **Choice preserved.** Some trait surfaces want to be reusable, separately-governed artifacts; others want to stay private to a single host. The chosen option should allow both.

## Considered Options

- Option 1 — Trait-type as a separately-registered GTS Type (URI value)
- Option 2 — `x-gts-traits-schema` is a JSON Schema subschema, in two sub-variants:
  - Option 2A — Subschema + implicit chain aggregation *(chosen)*
  - Option 2B — Subschema + explicit composition by the author

Option 2's sub-variants share the keyword's value space and differ only in who composes the declarations along the chain; they are evaluated inside Option 2 below.

### Option 1 — Trait-type as a separately-registered GTS Type (URI value)

`x-gts-traits-schema` is a **URI string** pointing at another registered GTS Type Schema that *is* the trait shape:

```jsonc
// Separately registered trait-type
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user_traits.v1~",
  "type": "object",
  "properties": { "retention": { "type": "string" } }
}

// Base host type — Option 1
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~",
  "type": "object",
  "required": ["id", "name"],
  "properties": {
    "id":   { "type": "string" },
    "name": { "type": "string" }
  },
  "x-gts-traits-schema": "gts://gts.x.example.user_traits.v1~"
}

// Derived host type — Option 1
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": {
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  },
  "x-gts-traits-schema":
    "gts://gts.x.example.user_traits.v1~vendor.premium_user_traits.v1~"
}
```

For derivation, a separate **trait-type chain** must be expressed somehow — typically the descendant registers a derived trait-type (`...~vendor.premium_user_traits.v1~`) and points its host at it. GTS must then specify a rule for how host-type and trait-type chains relate (parallel derivation? URN-prefix matching? something else?).

**Cons:**

- **Always requires a separate registered type.** Overkill for the common case where a trait shape is fully local and has no reuse story. Pollutes the type namespace; vendors may not want every internal trait shape to be a publicly enumerable type.
- **Requires a parallel concept in the spec.** "Trait-type" and "trait-type derivation chain" become first-class registry concepts, with their own rules for how they relate to the host chain. ADR-0001 deliberately avoids this kind of layered complexity.
- **Registration ordering / lifecycle coupling.** The trait-type MUST be registered before any host that references it; cascade deletion and version bumps span two lifecycles.
- **Versioning friction.** Bumping a trait-type's version is a separate event from bumping the host's version; authors must coordinate the two.
- **Conceptual mismatch.** Trait-type instances make no sense — traits are metadata about a type, not instance shapes — yet a first-class GTS Type by definition has an instance space. The model invites misuse.
- **Mixing inline + shared is impossible.** A host that wants to combine an inline trait field with a shared trait shape cannot do so cleanly: it either picks the URI form (no inline) or duplicates the shared shape inline.
- **Removes the choice on ACLs.** A separately-registered trait-type has its own access-control surface, distinct from the host's. Sometimes that's exactly what a vendor wants (reusable trait-schema with its own governance); sometimes it's pure overhead (trait shape is private to one host and should inherit the host's ACL). Option 1 always forces the separate-ACL outcome; Option 2 preserves the choice (see "patterns within Option 2" below).

**Pros:**

- Reusable trait surfaces are explicitly first-class — but Option 2 covers this via `$ref` inside the subschema, so the pro is not exclusive.

### Option 2 — `x-gts-traits-schema` is a JSON Schema subschema

`x-gts-traits-schema` is an ordinary [JSON Schema subschema](https://json-schema.org/learn/glossary#subschema) embedded directly inside the host type. With this one framing the spec dispenses with a whole category of questions: yes, the value may contain `$ref`; yes, it may contain `allOf`; yes, it may declare `properties` / `required` / etc. — standard JSON Schema applies, because the value *is* a JSON Schema.

**A subschema is an *object* OR a *boolean*** (per the JSON Schema glossary). Both forms are admissible for `x-gts-traits-schema`:

- `"x-gts-traits-schema": { ... }` — an object subschema declares the trait shape in the usual way.
- `"x-gts-traits-schema": true` — the empty schema. **Any trait values pass**: traits are permitted but unconstrained at this layer.
- `"x-gts-traits-schema": false` — the unsatisfiable schema. **No traits are permitted** on this host and on any descendant whose chain includes this layer (`false` makes the chain-aggregated effective trait-schema unsatisfiable). Useful for a base type that wants to prohibit traits entirely, or for a leaf type that wants to opt out.

Worked example, base host type:

```jsonc
// Base host type — Option 2, object-form subschema
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~",
  "type": "object",
  "required": ["id", "name"],
  "properties": {
    "id":   { "type": "string" },
    "name": { "type": "string" }
  },
  "x-gts-traits-schema": {
    "type": "object",
    "properties": { "retention": { "type": "string" } }
  }
}
```

#### Patterns within Option 2

Two patterns coexist under the same keyword:

- **Inline.** The trait shape is declared inline inside the host. Trait shape is private; host's ACL applies; no separate registered artifact. (Used in the base host above.)
- **Standalone trait-schema referenced via `$ref`.** A vendor publishes a trait-schema as an ordinary GTS Type and references it from hosts:

  ```jsonc
  // Standalone trait-schema, registered as an ordinary GTS Type
  { "$id": "gts://gts.x.example.traits.user_meta.v1~", "type": "object", ... }

  // Host references it inside the subschema
  "x-gts-traits-schema": {
    "allOf": [{ "$ref": "gts://gts.x.example.traits.user_meta.v1~" }],
    "properties": { "tenantScoped": { "type": "boolean" } }
  }
  ```

The standalone trait-schema is a normal registered GTS Type, governed by its own ACL — *when the vendor explicitly wants that*. Hosts that don't want a separately-governed artifact use the inline pattern. Both shapes are produced by the same keyword semantics; this is a pattern within Option 2, not a separate option.

Two sub-variants on **how trait-schemas compose under host-type derivation**:

#### Option 2A — Implicit aggregation along the `$id` chain *(chosen)*

The registry's *effective* `x-gts-traits-schema` for a host type T is the JSON Schema `allOf` composition of all `x-gts-traits-schema` declarations encountered along T's host-type derivation chain, root → leaf. The descendant author writes only the **delta** (new fields, narrowed constraints, additional `$ref`s) in their own `x-gts-traits-schema`; the inheritance is performed by the registry.

Worked example — descendant adds `supportLevel`:

```jsonc
// Derived host type — Option 2A
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": {
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  },
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "supportLevel": { "type": "string", "enum": ["standard", "priority"] }
    }
  }
}
```

The author does not repeat the ancestor's `retention` property inside `x-gts-traits-schema`. The registry composes via `allOf` along the `$id` chain, so the effective trait-schema for `premium_user.v1~` is equivalent to:

```jsonc
{
  "allOf": [
    { "type": "object", "properties": { "retention":    { "type": "string" } } },
    { "type": "object", "properties": { "supportLevel": { "type": "string", "enum": ["standard","priority"] } } }
  ]
}
```

By construction, any value satisfying the effective trait-schema also satisfies every ancestor's — so **trait-schema compatibility under derivation is automatic and structural**, no separate "narrowing" check needed.

#### Option 2B — Explicit composition by the author

`x-gts-traits-schema` is still a JSON Schema subschema, but the spec does NOT pre-compose declarations along the host chain. If the descendant wants the ancestor's trait fields, the author writes the composition by hand inside their own `x-gts-traits-schema`:

```jsonc
// Derived host type — Option 2B
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": {
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  },
  "x-gts-traits-schema": {
    "allOf": [
      { "$ref": "gts://gts.x.example.user.v1~#/x-gts-traits-schema" },
      {
        "type": "object",
        "properties": {
          "supportLevel": { "type": "string", "enum": ["standard", "priority"] }
        }
      }
    ]
  }
}
```

#### 2A vs 2B trade-off

- **2A pros.** Less boilerplate; lower chance of accidentally dropping ancestor traits (forgetting `allOf` in 2B silently strips inheritance); symmetric with the extension framing in ADR-0001.
- **2A cons.** Requires one explicit GTS rule — "the registry composes `x-gts-traits-schema` along the `$id` chain via `allOf`." This is a genuine GTS-specific rule (JSON Schema does not define cross-`$ref` annotation aggregation in any dialect). One sentence in the spec.
- **2B pros.** No GTS-specific aggregation rule — the trait subschema is a plain JSON Schema subschema, full stop. Symmetric with how a derived host body uses explicit `allOf` + `$ref` for parent fields.
- **2B cons.** Boilerplate; the failure mode (forgetting `allOf`) is a *silent drop* of inherited traits rather than a visible error; awkward `$ref` syntax for fragments into another schema document (`gts://...~#/x-gts-traits-schema`).

## Decision Outcome

Chosen option: **Option 2A — `x-gts-traits-schema` is a JSON Schema subschema (object OR boolean); the registry composes declarations along the `$id` chain via `allOf`.**

Normative consequences:

- `x-gts-traits-schema` is an ordinary JSON Schema subschema. Its value MAY be:
  - a JSON object — declares the trait shape in the usual way;
  - `true` — any trait values pass (no constraint);
  - `false` — no traits permitted on this host (and unsatisfiable in chain aggregation, so any descendant chain containing `false` allows no traits either).
- The *effective* `x-gts-traits-schema` of a host type T is the `allOf` composition of all `x-gts-traits-schema` declarations encountered along T's `$id` chain, root → leaf. The author writes only the delta; the registry aggregates.
- Compatibility of a descendant's trait-schema with its ancestor's is **automatic and structural** — every value satisfying the effective trait-schema also satisfies the ancestor's declaration by construction.
- A descendant MAY write its own `x-gts-traits-schema` as an explicit `allOf` that includes a `$ref` to an ancestor's `x-gts-traits-schema`. Doing so is **redundant under 2A** (the registry already aggregates) but **not invalid** — outlawing it would violate the ADR-0001 principle "any syntactically valid JSON Schema is a syntactically valid GTS Type Schema."
- A vendor MAY publish a standalone trait-schema as an ordinary GTS Type and reference it from hosts via `$ref` inside `x-gts-traits-schema`. This is a pattern within Option 2, not a separate option. It is the right choice when the vendor wants the trait surface to have its own governance / lifecycle / ACL; the inline form is the right choice otherwise.

### Implications

- **README §9.7** is updated to reflect this ADR — `x-gts-traits-schema` is named as a JSON Schema subschema (with glossary link), the boolean forms are made explicit, and the chain-aggregation rule is stated where readers expect to find it.
- **OP#13 (Schema Traits Validation)** is unchanged in scope — it remains the operation that validates effective trait-schemas and effective trait values.
- **`additionalProperties` inside a trait-schema.** The Draft-07 `$ref`+siblings / `$ref`+`additionalProperties: false` footgun (resolved in Draft 2019-09+ via `unevaluatedProperties`) applies inside `x-gts-traits-schema` exactly as it applies inside the host body when the dialect is Draft-07. Acknowledged and explicitly deferred to a separate discussion (same disposition as in ADR-0001).
- **Value side (`x-gts-traits`).** Out of scope of this ADR; covered in §9.7.3–§9.7.5.
- **Reference implementations (gts-go, gts-rust)** must support the boolean subschema form for `x-gts-traits-schema` and the chain-aggregation behaviour described above.
- **Backward compatibility.** The keyword's value space gains the boolean form; existing object-form schemas remain valid.

## Pros and Cons of the Options

### Option 1 — Trait-type as separate registered GTS Type

- **+** Reusable trait surfaces are first-class (not exclusive — Option 2 covers this via `$ref`).
- **−** Forces a parallel registry concept; lifecycle / versioning / ACL coupling; no inline option.
- **−** Removes the inline-vs-registered choice that vendors actually need.
- **−** Conceptual mismatch — trait-types have no meaningful instance space, but first-class GTS Types by definition have one.
- **−** Mixing inline + shared is impossible without duplication.

### Option 2A — Subschema + implicit chain aggregation (chosen)

- **+** One sentence of GTS-specific rule; everything else falls out of standard JSON Schema.
- **+** Symmetric with the ADR-0001 extension framing.
- **+** Trait-schema compatibility under derivation is automatic and structural.
- **+** Admits boolean subschema forms (`true` / `false`) naturally — useful for "no constraint" and "no traits allowed" cases.
- **+** Preserves the inline-vs-registered choice via the standalone-trait-schema-by-`$ref` pattern.
- **−** Requires authors to know that chain aggregation happens at the registry level (not visible in the schema text itself).

### Option 2B — Subschema + explicit composition by author

- **+** Zero GTS-specific aggregation rule; trait subschema is "just" a JSON Schema subschema.
- **−** Silent-failure mode — forgetting `allOf` strips inheritance with no visible error.
- **−** Awkward `$ref` syntax for cross-document fragment references into another schema.
- **−** Per-descendant boilerplate that scales with chain depth.

## More Information

Cross-references inside this specification: §9.7 (`x-gts-traits-schema` / `x-gts-traits`), §11.0 (Relationship to JSON Schema), §3.2 (GTS Types Inheritance), OP#13 (Schema Traits Validation). Related ADR: [`adr/0001-derivation-form.md`](0001-derivation-form.md) — the extension framing this ADR inherits.

External references:

- [JSON Schema subschema (glossary)](https://json-schema.org/learn/glossary#subschema)
- [JSON Schema Dialect (glossary)](https://json-schema.org/learn/glossary#dialect)
- [`allOf` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/combining#allof)
