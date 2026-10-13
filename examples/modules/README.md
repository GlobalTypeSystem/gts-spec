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

- `type` uses `x-gts-type-ref: "/$id"` and accepts a Type ID rooted at the selected leaf schema. Capability `id`, module `capabilities`, and module `requirements` use `x-gts-instance-ref` and accept only Instance IDs.
- A Type ID operand defines a family: it can constrain type references or instance references. `/$id` is supported by both keywords and resolves to the selected leaf Type ID, including inherited constraints. See [README §9.6.1](../../README.md#961-entity-references-x-gts-type-ref--x-gts-instance-ref).
- Registry lookup follows the selected `gts-ref-validation` mode: `none` checks operand validity and candidate syntax, kind, and matching; `any-present` additionally requires registered operand/candidate targets; `any-valid` additionally requires valid targets. A wildcard operand needs at least one registered match, valid under `any-valid`, while the candidate independently needs the required kind. REST validation defaults to `any-valid` when the parameter is omitted.
- The common validation lifecycle, including deferred checks with `validate=false`, is defined in [README §9.6.3](../../README.md#963-common-validation-rules).
