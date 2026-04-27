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

- `x-gts-ref` marks that a string field must be a valid GTS identifier:
  - `"gts..."` — any valid GTS ID of the referenced family.
  - `"./$id"` — self-reference to the current JSON Schema’s `$id`.
- These examples are illustrative and can be used to test parsing, validation, and reference resolution in GTS-aware tooling.
