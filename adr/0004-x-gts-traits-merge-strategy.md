# ADR-0004: `x-gts-traits` merge strategy — JSON Merge Patch (RFC 7396) along the `$id` chain

- **Status:** Accepted
- **Date:** 2026-05-27
- **Deciders:** GTS spec maintainers
- **Consulted:** —
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

### What `x-gts-traits` does

A GTS type carries trait values via `x-gts-traits` (a plain JSON object), validated against the effective trait-schema declared by `x-gts-traits-schema` (per ADR-0002). Trait values configure system behaviour — retention, indexing, routing, association links, compliance classifications — and do not appear in instance payloads.

### The chain question

A `$id` chain like `A~ → B~ → C~` may have `x-gts-traits` declared at any subset of the layers. The registry computes an *effective traits object* per type by combining those declarations. The spec must commit to:

- Whether declarations from ancestors flow into descendants at all (merge or no merge).
- If they do, how shared keys are resolved (override vs lock).
- If they do, how nested object values combine (shallow vs deep).

### Traits do not affect derivation compatibility

Unlike the host type's `properties` / `required` / `additionalProperties` (which DO participate in OP#12), `x-gts-traits` values are publisher metadata. They configure how the system treats instances of the type; they do not constrain instance payloads. The merge semantic can therefore be chosen for ergonomics and clarity, not for compatibility-preservation.

### Worked example

A base event type sets a default retention; a vendor wants either (a) to inherit it silently or (b) to specialize for their own derived event type. Different merge rules give different outcomes:

```jsonc
// Base event type
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "retention": { "type": "string", "default": "P30D" },
      "indexed":   { "type": "boolean", "default": false }
    }
  },
  "x-gts-traits": { "retention": "P30D" }
}

// Derived event type — wants 90-day retention for its own subtree
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": "P90D" }
}
```

What is the effective traits object for `audit.v1~`?

- Under **no merge**: `{ "retention": "P90D" }` (ancestor's `x-gts-traits` is invisible).
- Under **shallow last-wins merge**: `{ "retention": "P90D" }` (descendant wins) plus any other keys from ancestor not overridden.
- Under **shallow immutable-once-set**: registration fails — `retention` was claimed by the ancestor with `"P30D"`, descendant's `"P90D"` conflicts.
- Under **per-property keyword**: depends on how the trait-schema declares the property's merge behaviour.

The ADR commits to one of these choices.

## Decision Drivers

- **Ergonomics for the common case.** Authors should be able to specialize a trait in a descendant without ceremony — the OOP-override mental model. Forbidding the natural override puts friction on legitimate use.
- **Publisher's ability to lock values.** A publisher who really wants a trait fixed across all descendants should have a clear, standard mechanism — without inventing a GTS-specific keyword.
- **Predictability.** The merge semantic should be easy to read off the chain, with no surprises about nested object behaviour, array semantics, or `null` interpretations.
- **No GTS-specific machinery if JSON Schema already provides it.** ADR-0001 framing: extend JSON Schema with rules only when necessary; lean on existing constructs (`const`, `default`) where they fit.

## Considered Options

- Option 1 — No merge (each type self-contained)
- Option 2a — Shallow merge, descendant-last-wins
- Option 2b — Shallow merge, immutable-once-set (the rule in spec versions up to 0.11)
- Option 2c — RFC 7396 (JSON Merge Patch), descendant-last-wins *(chosen)*
- Option 3 — Per-property author-controlled merge

### Option 1 — No merge (each type self-contained)

Every type's `x-gts-traits` is read as the whole truth for that type alone. Ancestor declarations are ignored when computing the descendant's effective traits. (Defaults from the effective trait-schema still materialize per ADR-0003, since defaults live in the schema, not in `x-gts-traits`.)

*Example.* Base sets two trait values; derived sets none.

```jsonc
// Base
{
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "retention": { "type": "string" },
      "topicRef":  { "type": "string" }
    }
  },
  "x-gts-traits": { "retention": "P30D", "topicRef": "events" }
}

// Derived — no x-gts-traits
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }]
}
```

Effective traits object for `audit.v1~` under Option 1: `{}` — the base's `retention` and `topicRef` are invisible. If `audit.v1~` wants either, it must restate them locally.

- **+** Trivially simple semantics. No merge algorithm at all.
- **+** No override / locking question; each type stands alone.
- **−** Massive boilerplate: every derived type must restate every trait it inherits, or it loses them.
- **−** Defaults from `x-gts-traits-schema` (used by ADR-0003 materialization) become the *only* inheritance path; explicit `x-gts-traits` on ancestors becomes documentation that no descendant actually uses.

### Option 2a — Shallow merge, descendant-last-wins

The effective traits object is computed by walking the chain root → leaf and applying each `x-gts-traits` object via shallow object assignment: top-level keys from later layers overwrite those from earlier layers. Object-valued traits are replaced wholesale (not recursively merged). Publishers who need to lock a value declare `"const": <value>` for that property in `x-gts-traits-schema`; the standard JSON Schema validation that runs over the effective traits object (per ADR-0003) catches any descendant attempting to override.

*Example.* Base sets two trait values; derived overrides one.

```jsonc
// Base
{
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "retention": { "type": "string" },
      "topicRef":  { "type": "string" }
    }
  },
  "x-gts-traits": { "retention": "P30D", "topicRef": "events" }
}

// Derived — only restates retention
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": "P90D" }
}
```

Effective traits object for `audit.v1~` under Option 2a: `{ "retention": "P90D", "topicRef": "events" }`. The descendant's `retention` wins; `topicRef` is inherited.

- **+** Matches the OOP-override intuition most authors bring.
- **+** No GTS-specific lock mechanism needed — `const` in the trait-schema does the job, validated by ordinary JSON Schema. The publisher decides on a per-property basis (and the spec footprint stays small).
- **+** Simple to reason about: read root → leaf, latest declaration wins, no recursion.
- **+** Compatible with ADR-0003's "chain-merged then materialized" model — the materialization step (defaults applied for missing keys) composes cleanly after the merge.
- **−** Object-valued traits replace wholesale; if a publisher uses a nested trait shape (`routing: { topic, partitionKey }`), a descendant that overrides `routing` must restate every nested field they want to keep. In practice authors should prefer flat trait shapes, or use per-field traits rather than nested objects.
- **−** A descendant can change an ancestor's value the publisher *intended* to be fixed, if the publisher forgot to declare `const`. The mitigation is convention + linting; the spec gives the tool but does not enforce its use.

### Option 2b — Shallow merge, immutable-once-set

The effective traits object is computed by walking the chain root → leaf; once a key has been set by any layer, later layers MUST either omit it or repeat the same value. Conflicting redeclaration causes registration to fail.

**This was the normative rule in spec versions up to 0.11** (§9.7.5 "Immutable-once-set", together with "Immutable defaults" on the schema side). Rejecting it here is therefore a breaking change, not a newly filled gap — see the Backward compatibility note under Implications.

*Example.* Using the same base as Option 2a (`retention: "P30D"` declared on the base):

```jsonc
// Derived A — tries to override
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": "P90D" }   // ← conflict
}
```

Registration of derived A FAILS under Option 2b — `retention` was already claimed by the base as `"P30D"`, and the descendant's `"P90D"` is a different value.

```jsonc
// Derived B — repeats the same value (allowed, idempotent)
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": "P30D" }
}
```

Registration of derived B SUCCEEDS — value matches.

```jsonc
// Derived C — omits the key entirely
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }]
}
```

Registration of derived C SUCCEEDS; effective traits inherit `retention: "P30D"` from the base.

- **+** Ancestor's declaration is authoritative — descendants cannot silently break a publisher's policy.
- **+** Idempotent same-value repetition is permitted, so descendants who want to "re-state for documentation" can.
- **−** Brittle to authoring evolution: a chain authored bottom-up (descendant first, then ancestor populated) can fail when the ancestor adds a value that's already been claimed below.
- **−** Validation is more complex than standard JSON Schema — needs a chain-aware "first occurrence wins; later occurrences must match" check.
- **−** Contrary to the OOP-override mental model; trips up authors who expect descendants to specialize.
- **−** Redundant with `const`: a publisher who wants to lock a trait already has `const` in the trait-schema. The immutability rule duplicates this guarantee for the cases where the publisher *forgot to declare* `const` — which is arguably the wrong place to bake the safety net (it surprises the descendant author rather than nudging the publisher to be explicit).

### Option 2c — RFC 7396 (JSON Merge Patch), descendant-last-wins *(chosen)*

The merge follows RFC 7396 semantics: object values merge recursively (nested objects combine); arrays replace wholesale; `null` deletes a key. Override is last-wins (same as 2a) at the leaf level, but nested objects compose rather than replace.

*Example.* Use a nested-object trait to expose the difference from Option 2a.

```jsonc
// Base
{
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "routing": {
        "type": "object",
        "properties": {
          "topic":        { "type": "string" },
          "partitionKey": { "type": "string" }
        }
      }
    }
  },
  "x-gts-traits": {
    "routing": { "topic": "events", "partitionKey": "userId" }
  }
}

// Derived — overrides only `topic`
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": {
    "routing": { "topic": "orders" }
  }
}
```

Effective traits for `audit.v1~`:

- Under **Option 2a (shallow)**: `{ "routing": { "topic": "orders" } }` — `partitionKey` is **lost** because the whole `routing` object is replaced wholesale.
- Under **Option 2c (RFC 7396)**: `{ "routing": { "topic": "orders", "partitionKey": "userId" } }` — `partitionKey` is preserved by the recursive merge.

This is the main practical difference between Options 2a and 2c. If a descendant wanted to actively "delete" `partitionKey` under 2c, it could write `"partitionKey": null`.

- **+** Standard, well-defined semantics with mature implementations.
- **+** Preserves nested fields automatically.
- **−** `null` semantics ("delete this key") is a foreign concept for traits — traits aren't usually "removed," they're either set or absent. Authors who write `null` for a different reason would get surprised by the delete behaviour.
- **−** Array semantics (always replace) is a defensible choice but introduces a sub-rule readers have to remember; under shallow we don't say anything about arrays at all (because objects don't combine recursively in the first place).
- **−** "What does the effective traits object look like?" becomes a non-trivial computation; harder to predict by reading the schemas top-to-bottom.

### Option 3 — Per-property author-controlled merge

A new GTS keyword inside `x-gts-traits-schema` (e.g., `x-gts-trait-merge: "lock" | "override" | "deep-merge"`) lets the publisher declare per-property how merging behaves.

*Example.* Publisher locks `retention` but allows override of `topicRef`:

```jsonc
// Base
{
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "retention": {
        "type": "string",
        "x-gts-trait-merge": "lock"
      },
      "topicRef": {
        "type": "string",
        "x-gts-trait-merge": "override"
      }
    }
  },
  "x-gts-traits": { "retention": "P30D", "topicRef": "events" }
}

// Derived — tries to override both
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": {
    "retention": "P90D",   // ← rejected: property locked
    "topicRef":  "audit"   // ← accepted: override allowed
  }
}
```

Registration of the derived type fails at `retention` (locked). To succeed, the descendant must drop the `retention` override.

- **+** Maximum flexibility — different traits get different inheritance contracts.
- **−** Adds new spec vocabulary that every implementation must implement and every author must learn.
- **−** Multiple modes multiply test surface; conformance suite grows.
- **−** Mostly redundant with `const` + default behaviour: most legitimate needs (lock vs override) are already expressible without the new keyword. The remaining cases (deep-merge per property) are rare and can be re-visited later if real demand surfaces.

## Decision Outcome

Chosen option: **Option 2c — RFC 7396 (JSON Merge Patch) along the `$id` chain, descendant-last-wins at the leaf, with `const` in `x-gts-traits-schema` as the publisher's lock mechanism.**

### Normative consequences

- The *effective traits object* of a GTS type T is computed by walking T's `$id` chain root → leaf, treating the chain-merged object so far as the "target" and each layer's `x-gts-traits` as a JSON Merge Patch (RFC 7396) applied to it. At the leaf (top-level scalar value, array, or `null`), descendant declarations replace ancestor declarations (last-wins). For object-valued top-level keys, the recursion descends and the same patch semantics apply to nested fields.
- **Arrays replace wholesale** at any level (per RFC 7396). If a publisher needs item-level composability of an array trait, they SHOULD model that as a top-level keyed object instead of an array.
- **`null` at any level deletes that key** from the effective object (per RFC 7396). The principal use case is to revert an ancestor-set value and let the trait-schema's `default` re-apply via ADR-0003 materialization — see Worked example D. A descendant writes `"<key>": null` to invoke this. If the deleted key is `required` with no `default`, the completeness check (ADR-0003) fails registration for non-abstract types — the descendant either has to mark itself abstract or accept that "delete + required + no default" is an unresolvable contract. Authors who want `null` as an *intended* trait value cannot express it via this merge and must use a sentinel value documented as part of the trait shape.
- A publisher who wants to **lock** a trait value across all descendants of a base type SHOULD declare `"const": <value>` for that property inside `x-gts-traits-schema`. A descendant that attempts to set a different value for that property will fail the standard JSON Schema validation that runs over the effective traits object (per ADR-0003) — no GTS-specific lock rule is needed.
- A publisher who wants to provide a **soft default** that descendants may override SHOULD declare `"default": <value>` for that property. ADR-0003's materialization step applies the default if no chain-merged value is present.
- A descendant MAY redeclare a trait value with the same value the ancestor already declared (idempotent restatement, useful for documentation). This is naturally permitted by last-wins.

### Worked example A — natural override (last-wins)

Base type sets `retention` via `x-gts-traits`; descendant overrides:

```jsonc
// Base
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "retention": { "type": "string" },
      "topicRef":  { "type": "string" }
    }
  },
  "x-gts-traits": { "retention": "P30D", "topicRef": "events" }
}

// Derived — wants 90-day retention
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": "P90D" }
}
```

Effective traits for `audit.v1~`: `{ "retention": "P90D", "topicRef": "events" }`. `retention` is the descendant's value (last-wins); `topicRef` carried in from the chain. Both registrations succeed.

### Worked example B — nested-object trait, recursive merge

This is the case where JSON Merge Patch semantics show their value: a descendant updating one field of a nested-object trait without restating the others.

```jsonc
// Base
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "routing": {
        "type": "object",
        "properties": {
          "topic":        { "type": "string" },
          "partitionKey": { "type": "string" }
        }
      }
    }
  },
  "x-gts-traits": {
    "routing": { "topic": "events", "partitionKey": "userId" }
  }
}

// Derived — overrides only `topic`
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": {
    "routing": { "topic": "orders" }
  }
}
```

Effective traits for `audit.v1~`: `{ "routing": { "topic": "orders", "partitionKey": "userId" } }`. The descendant's `topic` overrides; `partitionKey` is preserved because RFC 7396 descends into `routing` and patches at the leaf level.

A descendant that actively wants to remove `partitionKey` writes it as `null`:

```jsonc
{
  "$id": "gts://gts.x.example.event.v1~vendor.unkeyed.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": {
    "routing": { "partitionKey": null }
  }
}
```

Effective traits: `{ "routing": { "topic": "events" } }`. `partitionKey` is gone (RFC 7396 delete semantics); `topic` is inherited unchanged.

### Worked example C — locking values via `const`

A publisher who wants `indexed` fixed across all descendants declares it `const` inside `x-gts-traits-schema`. No new GTS keyword is needed — the JSON Schema `const` keyword is the lock mechanism, validated by the ordinary JSON Schema validation that ADR-0003 already runs over the effective traits object.

```jsonc
// Base — locks `indexed` to true; allows `retention` to be overridden
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "retention": { "type": "string", "default": "P30D" },
      "indexed":   { "type": "boolean", "const": true }
    }
  },
  "x-gts-traits": { "indexed": true }
}
```

Descendant A — overrides `retention` only, leaves `indexed` alone:

```jsonc
{
  "$id": "gts://gts.x.example.event.v1~vendor.audit.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": "P90D" }
}
```

Effective traits: `{ "retention": "P90D", "indexed": true }`. **Succeeds** — `retention` is freely overridable, `indexed` is preserved from the chain. Validates against the effective trait-schema (`indexed: true` satisfies `const: true`).

Descendant B — tries to override the locked value:

```jsonc
{
  "$id": "gts://gts.x.example.event.v1~vendor.adhoc.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "indexed": false }
}
```

Effective traits after merge: `{ "indexed": false }` (descendant's value wins the merge — last-wins doesn't pre-judge values). But the materialized object is then validated against the effective trait-schema, which says `indexed: { "const": true }`. `false ≠ true` → JSON Schema validation fails → registration **fails**. The lock is enforced entirely by standard JSON Schema; the spec does not need a GTS-specific "immutable" rule to achieve it.

**Pattern.** Publisher chooses, per-property, in `x-gts-traits-schema`:

- `"const": <value>` — the value is **locked**; descendants that try to set anything else fail JSON Schema validation.
- `"default": <value>` — the value is a **soft default**; descendants who don't set the property inherit it, descendants who do set it can override freely (last-wins).
- neither — the property is open; descendants set or inherit values as they wish.

`const` locks the **value**, not the presence: JSON Schema asserts nothing about an absent property, so a descendant can still drop a `const`-constrained trait with an RFC 7396 `null` patch. This is the general presence rule for traits, not a `const`-specific gap — any optional inherited trait without a `default` is removable the same way. A publisher who wants presence guaranteed too picks one of:

- add the property to the containing object schema's `required` array — the deletion then fails the ADR-0003 completeness check for non-abstract types (loud failure);
- declare a `default` equal to the `const` value — the deletion becomes a no-op, since materialization restores the value before validation (self-healing).

### Worked example D — `null` to fall back to the trait-schema default

The main motivation for the `null`-as-delete semantic from RFC 7396 is its clean interaction with ADR-0003 *materialization*: after the chain-merge produces the effective traits object, defaults declared in the effective trait-schema are applied for properties **not present** in that object. A descendant that writes `"<key>": null` therefore removes the chain-merged value for that key, and the materialization step then fills it back in from the schema's `default` (if any).

Example: ancestor opinionates the value to a non-default; a specific descendant wants to revert to the schema default without picking its own specific value.

```jsonc
// Base — schema default is "P7D", ancestor opinionates to "P30D"
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.event.v1~",
  "x-gts-traits-schema": {
    "type": "object",
    "properties": {
      "retention": { "type": "string", "default": "P7D" }
    }
  },
  "x-gts-traits": { "retention": "P30D" }
}

// Derived — revert to the schema default
{
  "$id": "gts://gts.x.example.event.v1~vendor.shortlived.v1~",
  "allOf": [{ "$ref": "gts://gts.x.example.event.v1~" }],
  "x-gts-traits": { "retention": null }
}
```

Effective traits computation for `shortlived.v1~`:

1. Chain-merge: start from `{}`, apply ancestor's patch → `{ "retention": "P30D" }`; apply descendant's patch with `null` at the leaf → `{}` (key removed).
2. ADR-0003 materialization: `retention` is missing; the effective trait-schema declares `default: "P7D"`; substitute → `{ "retention": "P7D" }`.

Effective traits: `{ "retention": "P7D" }`. The descendant successfully reverted to the schema default.

**Failure mode.** If the deleted key is `required` in the effective trait-schema AND has no `default`, then after merge + materialization the required field remains unresolved. For a non-abstract type, the completeness check (ADR-0003) fails registration. Authors who genuinely need to delete a `required`-without-`default` trait must mark the type `x-gts-abstract: true` (i.e., explicitly declare "this layer doesn't satisfy the contract; descendants will").

### Edge cases

- **Object-valued trait, descendant overrides one nested field.** Per Worked example B: ancestor's other nested fields are preserved; only the field the descendant restates is overridden. No need for descendants to restate the whole nested object.
- **Array-valued trait, descendant declares a different array.** Arrays replace wholesale (per RFC 7396). If publishers need per-element composability, they should model the data as a keyed object rather than an array.
- **`null` in `x-gts-traits` deletes the key.** Per RFC 7396, a leaf value of `null` removes that key from the effective object. The primary use case is letting ADR-0003 materialization re-apply the trait-schema's `default` for that key (see Worked example D). If the deleted key is `required` and has no `default`, the completeness check (ADR-0003) fails registration for non-abstract types. Authors who want `null` as an actual trait *value* cannot express it via this merge — they would need a sentinel (e.g., `"unset"`) and document it as part of the trait shape.
- **A `const`-constrained property is deleted with `null`.** If the property is also `required`, the completeness check fails and the lock holds. If it has a `default` equal to the `const` value, materialization restores it and the deletion is a no-op. If it is neither, its absence satisfies the schema — `const` asserts nothing about an absent property.
- **Ancestor sets a value; descendant repeats the same value.** Permitted; both layers agree.
- **No `x-gts-traits` anywhere in the chain.** Effective traits object is empty; ADR-0003's materialization fills in any defaults declared in the effective trait-schema; the completeness check (for non-abstract types) then validates the materialized object.
- **`x-gts-traits` on an abstract base.** Carried forward into descendants exactly like any other layer; abstract status affects only completeness checking per ADR-0003, not merge.

### Implications

- **§9.7.5 ("Trait merge and validation semantics")** carries the normative wording of RFC 7396 merge along the `$id` chain and the `const`-based lock mechanism.
- **ADR-0003** stays correct as written; the "chain-merged effective traits object" referenced there is now formally defined as the result of applying each layer's `x-gts-traits` as a JSON Merge Patch (RFC 7396) to the chain-merged object so far, root → leaf.
- **OP#13 description (§9.7)** is unaffected; it speaks generically of "chain-merged" values.
- **§9.11.4 (modifiers ↔ traits)** is unaffected; completeness keying on `x-gts-abstract` is independent of merge policy.
- **Reference implementations (gts-go, gts-rust)** must implement RFC 7396 merge along the chain. Available implementations exist in both ecosystems. The registry MUST NOT enforce a "different value MUST fail" rule on its own — it relies on standard JSON Schema validation against the effective trait-schema (which catches `const` violations naturally).
- **Conformance test suite** should exercise: (a) descendant overrides a top-level scalar — succeeds (last-wins); (b) descendant overrides one field of a nested-object trait — other nested fields preserved; (c) descendant overrides an array-valued trait — array replaces wholesale; (d) descendant writes `null` at a leaf — the key is removed; (e) descendant repeats the same value — succeeds (idempotent); (f) publisher locks via `const`, descendant attempts override — fails JSON Schema validation; (g) publisher locks via `const` and `required`, descendant attempts to delete the property with `null` — fails the completeness check; (h) chain with three layers; middle layer overrides base; leaf overrides middle.
- **Backward compatibility: breaking** (reflected in the README changelog entry for 0.12). This decision does not fill a gap — it reverses a prior normative rule. Spec versions up to 0.11 required "immutable-once-set" for trait values (a descendant supplying a different value for a key already set by an ancestor MUST fail validation) plus "immutable defaults" (a descendant MUST NOT redeclare an ancestor's `default`) — that is, Option 2b above, which this ADR rejects. Under RFC 7396 last-wins, a chain that MUST have been rejected now registers successfully, and locking becomes opt-in for the publisher via `const` instead of implicit. Implementations MUST remove the immutable-once-set and immutable-defaults checks; conformance tests asserting the old rejection MUST be rewritten. Registries that relied on the implicit guarantee SHOULD audit published base types and add `const` where a fixed trait value was intended.

## Pros and Cons of the Options

### Option 1 — No merge

- **+** Simplest semantics.
- **−** Boilerplate-heavy; defeats the point of declaring traits on ancestors.

### Option 2a — Shallow last-wins

- **+** Simplest merge algorithm.
- **+** Locking handled by existing `const`; no new GTS vocabulary.
- **−** Wholesale object replacement for nested traits; descendants must restate every nested field they want to keep, even if they only touch one. Pushes authors toward unnaturally flat trait shapes.

### Option 2b — Shallow immutable-once-set

- **+** Strong publisher guarantee.
- **−** Redundant with `const`; brittle to evolution; non-standard validation; contrary to OOP intuition.

### Option 2c — RFC 7396 (chosen)

- **+** Standard, well-specified merge semantics with mature implementations in major language ecosystems.
- **+** Preserves nested fields automatically — descendants can update one field of a nested-object trait without restating the rest.
- **+** Provides `null`-as-delete as a clean way for descendants to remove an inherited trait when needed.
- **+** Locking still handled by `const`; the GTS-side spec footprint remains tiny.
- **−** `null` carries delete semantics; authors who want `null` as a genuine trait value cannot express it via the merge and must use a sentinel.
- **−** Arrays replace wholesale at any depth — an extra sub-rule readers must remember, in exchange for predictable RFC 7396 semantics.
- **−** Predicting the effective traits object requires running the merge in head (more complex than reading shallow assignment). Mitigated by good tooling that displays the effective traits object.

### Option 3 — Per-property keyword

- **+** Maximum flexibility.
- **−** New vocabulary, larger spec surface, mostly redundant with `const` + last-wins for realistic needs.

## More Information

Cross-references inside this specification: §9.7 (`x-gts-traits-schema` / `x-gts-traits`), §9.11 (`x-gts-final` / `x-gts-abstract`), OP#13 (Schema Traits Validation). Related ADRs: [`adr/0001-derivation-form.md`](0001-derivation-form.md) (extension framing), [`adr/0002-x-gts-traits-schema.md`](0002-x-gts-traits-schema.md) (trait-schema as JSON Schema subschema with chain aggregation), [`adr/0003-x-gts-traits-completeness.md`](0003-x-gts-traits-completeness.md) (completeness check at type registration).

External references:

- [`const` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/generic#constant-values)
- [`default` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/annotations)
- [RFC 7396 — JSON Merge Patch](https://datatracker.ietf.org/doc/html/rfc7396)
