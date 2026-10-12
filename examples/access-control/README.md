# Access scope examples

An access scope pairs an action with a GTS resource selector. The examples use
the existing [VM identifier family](../typespec/vms/README.md).

- [Access scope](types/gts.x.core.iam.access_scope.v1~.schema.json) accepts any
  valid pattern with `x-gts-pattern-ref: "gts.*"`.
- [VM access scope](types/gts.x.core.iam.access_scope.v1~x.infra.compute.vm_scope.v1~.schema.json)
  derives through `allOf` + `$ref` and narrows the operand to
  `gts.x.infra.compute.vm.*`.
- [Three valid scopes](instances/gts.x.core.iam.access_scope.v1~x.infra.compute.vm_scope.v1~.examples.json)
  use UUID `id` values and an explicit `type`.

| `resource_pattern` | Selects |
|---|---|
| `gts.x.infra.compute.vm.*` | All VM versions and all derived types and instances. |
| `gts.x.infra.compute.vm.v1~` | VM major version 1 and all derived types and instances, with minor-version flexibility. |
| `gts.x.infra.compute.vm.v1~vmware.esxi.*` | VMware ESXi types and instances under VM major version 1. |

A concrete Type ID is already a pattern selecting the type and its descendants;
it needs no trailing `*`. The wildcard in `vm.*` replaces the version and also
covers other major versions, even if they have not been registered.

## Invalid values

Replacing `resource_pattern` in a valid VM scope with any value below fails:

| Value | Reason |
|---|---|
| `gts.x.core.events.*` | Different identifier family. |
| `gts.x.infra.compute.vm_state.*` | A different type token; a textual `vm` prefix is insufficient. |
| `gts.x.infra.compute.*` | A broader pattern that also selects non-VM identifiers. |
| `gts.x.infra.compute.vm.v1*` | Invalid wildcard boundary. |

## Validation

Register the base scope schema before the derived schema, then validate the
scope instances. VM types and instances need not be registered:
`x-gts-pattern-ref` checks syntax and coverage without a registry lookup.
Use a GTS-aware validator; generic JSON Schema validators may ignore the keyword.
See [README §9.6.2](../../README.md#962-pattern-valued-fields-x-gts-pattern-ref)
and [ADR-0007](../../adr/0007-gts-pattern-ref.md).
