# Advanced JSON Schema examples

This folder groups focused examples for JSON Schema features that recently
became important in the spec and conformance tests.

It is intentionally split by dialect:

- `types/` + `instances/` use **Draft-07** and are included in the existing CI
  schema compile command (`examples/*/types/*.schema.json`).
- `draft-2020-12/` demonstrates **Draft 2020-12** features (`$defs`,
  `unevaluatedProperties`) in a separate, self-contained sample.

## Draft-07 examples

- `types/gts.x.advanced.schema.login_event.v1~.schema.json`
  - Abstract base type with:
    - top-level `x-gts-traits-schema`
    - root JSON Pointer `x-gts-ref` (`"/$id"`)
    - required format assertions (`uuid`, `email`, `date-time`, `date`, `time`,
      `uri`, `hostname`, `ipv4`, `ipv6`, `regex`)
- `types/gts.x.advanced.schema.login_event.v1~x.demo.security.login_event.v1~.schema.json`
  - Derived concrete type with:
    - `allOf` + `$ref` derivation
    - local reusable `definitions` + local `$ref`
    - conditional validation (`if` / `then`)
    - top-level `x-gts-traits`
- `instances/gts.x.advanced.schema.login_event.v1~x.demo.security.login_event.v1~.examples.json`
  - Valid instances showing both conditional branches.

## Draft 2020-12 example

- `draft-2020-12/gts.x.advanced.schema.profile.v1~.schema.json`
  - Uses `$defs` and `unevaluatedProperties: false` to show dialect-specific
    object closure behaviour.
- `draft-2020-12/gts.x.advanced.schema.profile.v1~.example.json`
  - Valid instance for the 2020-12 schema.

Validate this sample with a dialect-aware command (outside the Draft-07 CI
glob), for example:

```bash
ajv compile -s "examples/advanced-json-schema/draft-2020-12/*.schema.json" --spec=draft2020 --strict=false
```
