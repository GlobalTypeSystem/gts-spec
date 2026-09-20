# Modules examples

This folder contains a simple self-contained examples for a pluggable SaaS service that supports modules with custom configs, and also needs to know modules capabilities in order to define API gateway properly

## Types (`types/`)

- `types/gts.x.core.modules.capability.v1~.schema.json` - Base schema for a capability
- `types/gts.x.core.modules.module.v1~.schema.json` - Base schema for a module. Fields:
    - `capabilities`: array of capabilities this module provides
    - `requirements`: array of required modules

## Instances (`instances/`)

- `gts.x.core.modules.capability.v1~x.core.api.has_ws.v1.json` — example capability (supports WebSocket)
- `gts.x.core.modules.capability.v1~x.core.api.is_rest.v1.json` — example capability (is REST)
- `gts.x.core.modules.capability.v1~x.core.api.is_sse.v1.json` — example capability (supports SSE)
- `gts.x.core.modules.module.v1~x.webstore._.catalog.v1.json` — example module (catalog)
- `gts.x.core.modules.module.v1~x.webstore._.chat.v1.json` — example module (chat)

## Notes

- `x-gts-ref` marks that a string field must be a valid GTS identifier (see §9.6). The operand is a valid concrete GTS identifier, a GTS wildcard pattern (§10), or exactly the reserved string `/$id`; all other slash-prefixed forms are prohibited:
  - `"gts.*"` (or any wildcard, e.g. `"gts.x.core.modules.capability.*"`, `"...v1~*"`) — the value must be a syntactically valid GTS ID that matches the pattern.
  - `"gts.<prefix>..."` — a concrete identifier: the value must be a valid GTS ID that matches it, where a `~`-terminated prefix matches the exact type and any entity derived from it (`gts.x...v1~` ≡ `gts.x...v1~` or `gts.x...v1~*`).
  - `"/$id"` — self-reference rooted at the leaf GTS Type Schema selected for validation, including when the constraint is inherited from a base schema.
  - Registry lookup follows the selected `gts-ref-validation` mode (§9.6): `none` checks syntax and matching only; `any-present` requires registered constraint/value targets without validating them; and `any-valid` requires valid targets. A wildcard constraint requires at least one registered match under `any-present` and at least one registered, valid match under `any-valid`. REST validation defaults to `any-valid` when the parameter is omitted.
- These examples are illustrative and can be used to test parsing, validation, and reference resolution in GTS-aware tooling.
