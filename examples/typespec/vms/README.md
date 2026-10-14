# Virtual Machine Examples (TypeSpec)

This directory contains GTS examples for virtual machine types across different virtualization platforms.

## Overview

These examples demonstrate:
- **Base VM type**: Common properties shared by all virtual machines
- **Derived VM types**: Platform-specific extensions for VMWare ESXi, Nutanix AHV, and Virtuozzo
- **Power states as GTS instances**: Well-known state values with vendor support

## Schema Definitions (TypeSpec)

### Base Type

- **[gts.x.infra.compute.vm.v1~](types/gts.x.infra.compute.vm.v1~.tsp)** ([JSON Schema](types/gts.x.infra.compute.vm.v1~.schema.json))
  - Base virtual machine type with common properties
  - Properties: `type`, `id`, `name`, `cpuCores`, `ramMb`, `powerState`, `osType`, `createdAt`, `environment`, `owner`, `metadata`
  - `type` uses `x-gts-type-ref`; `powerState` uses `x-gts-instance-ref` to reference a state instance

### Derived Types

- **[gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~](types/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~.tsp)** ([JSON Schema](types/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~.schema.json)) - VMWare ESXi
- **[gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~](types/gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~.tsp)** ([JSON Schema](types/gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~.schema.json)) - Nutanix AHV
- **[gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~](types/gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~.tsp)** ([JSON Schema](types/gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~.schema.json)) - Virtuozzo

## Power States (GTS Instance References)

The final power-state type is defined in `types/states/`. Each state below is a well-known instance in `instances/states/`; vendors can add state instances without deriving new types.

### Base State Type

- **[gts.x.infra.compute.vm_state.v1~](types/states/gts.x.infra.compute.vm_state.v1~.tsp)** ([JSON Schema](types/states/gts.x.infra.compute.vm_state.v1~.schema.json)) - Base power state type

### Stable States

| State | GTS ID |
|-------|--------|
| Running | `gts.x.infra.compute.vm_state.v1~x.infra._.running.v1` |
| Stopped | `gts.x.infra.compute.vm_state.v1~x.infra._.stopped.v1` |
| Suspended | `gts.x.infra.compute.vm_state.v1~x.infra._.suspended.v1` |
| Paused | `gts.x.infra.compute.vm_state.v1~x.infra._.paused.v1` |

### Transient States

| State | GTS ID | Description |
|-------|--------|-------------|
| Starting | `gts.x.infra.compute.vm_state.v1~x.infra._.starting.v1` | VM is booting |
| Stopping | `gts.x.infra.compute.vm_state.v1~x.infra._.stopping.v1` | VM is shutting down |
| Suspending | `gts.x.infra.compute.vm_state.v1~x.infra._.suspending.v1` | Saving state to disk |
| Rebooting | `gts.x.infra.compute.vm_state.v1~x.infra._.rebooting.v1` | VM is rebooting |
| Migrating | `gts.x.infra.compute.vm_state.v1~x.infra._.migrating.v1` | Live migration in progress |

### Vendor-Specific States

Vendors can publish custom state instances with identifiers such as:
```
gts.x.infra.compute.vm_state.v1~vmware.esxi._.paused_due_error.v1
```

## Instance Examples

- **[web-server-01.json](instances/vms/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~web-server-01.json)** - VMWare ESXi (4 CPU, 8GB)
- **[db-server-01.json](instances/vms/gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~db-server-01.json)** - Nutanix AHV (8 CPU, 32GB)
- **[app-server-01.json](instances/vms/gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~app-server-01.json)** - Virtuozzo (2 CPU, 4GB)

## GTS Identifier Pattern

```
gts.x.infra.compute.vm.v1~<vendor>.<platform>._.vm.v1~
```

## TypeSpec Compilation

```bash
npm install -g @typespec/compiler @typespec/json-schema
tsp compile types/gts.x.infra.compute.vm.v1~.tsp --emit @typespec/json-schema
```
