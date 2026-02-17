This folder contains **worked examples** showing how GTS identifiers are used for:

- **Types (schemas)**: always have a **GTS type identifier** (ends with `~`) and are represented as JSON Schemas in `./schemas/`.
- **Instances (objects)**: may be either:
  - **Well-known (named)** instances with a stable **GTS instance identifier** in `id` (often chained from the type), or
  - **Anonymous** instances with a UUID `id` and an explicit GTS **type** reference in `type`.

### Examples

**Well-known instance (topic/stream)**

Topics are commonly well-known instances (named streams). Example:

- `./instances/gts.x.core.events.topic.v1~x.commerce.orders.orders.v1.0.json`

The instance uses a chained GTS identifier in `id`:
- Left segment: `gts.x.core.events.topic.v1~` (the schema/type)
- Rightmost segment: `x.commerce._.orders.v1.0` (the instance name)

**Anonymous instance (event)**

Individual events are commonly anonymous: they use a UUID `id` but still declare their GTS type in `type`. Example:

- `./instances/gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1~.examples.json`

### Field name aliases (recommended)

If a payload cannot use `id` / `type`, implementations may also support:
- **Instance id**: `gtsId`, `gts_id`
- **Instance type**: `gtsType`, `gts_type`
