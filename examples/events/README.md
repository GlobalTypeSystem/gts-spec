This folder contains **worked examples** showing how GTS identifiers are used for:

- **GTS Types**: always have a **GTS Type Identifier** (ends with `~`) and are represented as JSON Schemas in `./types/`.
- **GTS Instances**: may be either:
  - **Well-known (named)** instances with a stable **GTS Instance Identifier** in `id` (often chained from the type), or
  - **Anonymous** instances with a UUID `id` and an explicit **GTS Type Identifier** reference in `type`.

### Examples

**Well-known instance (topic/stream)**

Topics are commonly well-known instances (named streams). Example:

- `./instances/gts.x.core.events.topic.v1~x.commerce.orders.orders.v1.0.json`

The instance uses a chained GTS identifier in `id`:
- Left segment: `gts.x.core.events.topic.v1~` (the GTS Type)
- Rightmost segment: `x.commerce._.orders.v1.0` (the instance name)

**Anonymous instance (event)**

Individual events are commonly anonymous: they use a UUID `id` but still declare their GTS type in `type`. Example:

- `./instances/gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1~.examples.json`

Alternative combined anonymous instance id form (type chain + UUID tail embedded into `id`):

- Schema: `./types/gts.x.core.events.type_combined.v1~.schema.json`
- Derived schema: `./types/gts.x.core.events.type_combined.v1~x.commerce.orders.order_placed.v1.0~.schema.json`
- Instance: `./instances/gts.x.core.events.type_combined.v1~x.commerce.orders.order_placed.v1.0~.examples.json`

### 3-level type derivation (base → abstract → concrete)

GTS supports multi-level type inheritance. The audit event family demonstrates a **3-level chain**:

| Level | GTS Type Identifier | Abstract? | Description |
|-------|---------------------|-----------|-------------|
| 1 — Base | `gts.x.core.events.type.v1~` | yes | Generic event envelope |
| 2 — Derived | `gts.x.core.events.type.v1~x.core.audit.type.v1~` | yes | Audit event — adds `action`, `actor_id`, `ip_address`, `user_agent` |
| 3 — Concrete | `gts.x.core.events.type.v1~x.core.audit.type.v1~x.core.iam.settings_changed.v1~` | no | IAM Settings Changed audit event |

Each level uses `allOf` + `$ref` to derive from its parent:

- **Level 2** schema: `./types/gts.x.core.events.type.v1~x.core.audit.type.v1~.schema.json`
- **Level 3** schema: `./types/gts.x.core.events.type.v1~x.core.audit.type.v1~x.core.iam.settings_changed.v1~.schema.json`
- **Topic**: `./instances/gts.x.core.events.topic.v1~x.core.audit.events.v1.json`
- **Instance**: `./instances/gts.x.core.events.type.v1~x.core.audit.type.v1~x.core.iam.settings_changed.v1~.examples.json`

### Field name aliases (recommended)

If a payload cannot use `id` / `type`, implementations may also support:
- **Instance id**: `gtsId`, `gts_id`
- **Instance type**: `gtsType`, `gts_type`
