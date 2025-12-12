# Virtual Machine Examples (TypeSpec)

This directory contains GTS examples for virtual machine types across different virtualization platforms.

## Overview

These examples demonstrate:
- **Base VM type**: Common properties shared by all virtual machines (CPU, RAM, power state, etc.)
- **Derived VM types**: Platform-specific extensions for VMWare ESXi, Nutanix AHV, and Virtuozzo
- **Type inheritance**: How derived types extend base types while maintaining compatibility

## Schema Definitions (TypeSpec)

TypeSpec is a language for describing APIs and generating schemas. These `.tsp` files define the structure of VM types using TypeSpec syntax.

### Base Type

- **[gts.x.infra.compute.vm.v1~](schemas/gts.x.infra.compute.vm.v1~.tsp)**
  - Base virtual machine type with common properties
  - Properties: `gtsId`, `id`, `name`, `cpuCores`, `ramMb`, `powerState`, `osType`, `createdAt`, `metadata`

### Derived Types

Each derived type extends the base VM with platform-specific properties stored in `metadata`:

- **[gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~](schemas/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~.tsp)**
  - VMWare ESXi virtual machine
  - Metadata contains: MoRef ID, host, datacenter, VMWare Tools status, hardware version, vMotion settings

- **[gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~](schemas/gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~.tsp)**
  - Nutanix AHV (Acropolis Hypervisor) virtual machine
  - Metadata contains: cluster UUIDs, protection domain, categories, storage container, HA priority

- **[gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~](schemas/gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~.tsp)**
  - Virtuozzo virtual machine
  - Metadata contains: VEID, environment type (VM/container), node info, storage cluster, HA settings

## Instance Examples (JSON)

The `instances/` directory contains concrete VM instance examples:

- **[web-server-01.json](instances/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~web-server-01.json)** - VMWare ESXi web server (4 CPU, 8GB RAM, Production)
- **[db-server-01.json](instances/gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~db-server-01.json)** - Nutanix AHV database server (8 CPU, 32GB RAM, High Priority)
- **[app-server-01.json](instances/gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~app-server-01.json)** - Virtuozzo application server (2 CPU, 4GB RAM, Staging)

## GTS Identifier Pattern

All VMs follow the GTS inheritance chain pattern:

```
gts.x.infra.compute.vm.v1~<vendor>.<platform>._.vm.v1~
```

Examples:
- `gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~`
- `gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~`
- `gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~`

## Use Cases

These examples demonstrate how GTS enables:

1. **Multi-cloud VM management**: Unified interface for VMs across different platforms
2. **Hybrid database storage**: Store common VM properties in indexed columns, platform-specific data in JSONB `metadata`
3. **Type-safe APIs**: Validate VM data against registered schemas before storage
4. **Access control**: Use GTS patterns to grant permissions (e.g., `gts.x.infra.compute.vm.v1~vmware.*`)

## TypeSpec to JSON Schema

To generate JSON Schema from TypeSpec files:

```bash
# Install TypeSpec compiler
npm install -g @typespec/compiler @typespec/json-schema

# Compile TypeSpec to JSON Schema
tsp compile gts.x.infra.compute.vm.v1~.tsp --emit @typespec/json-schema
```

## Validation

Validate instance examples against generated schemas:

```bash
# Using ajv-cli
npm install -g ajv-cli
ajv validate -s schemas/generated/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~.schema.json \
    -d instances/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~web-server-01.json
```

## Related Examples

- [Events Examples](../../events/) - Event-driven architecture with GTS
- [Modules Examples](../../modules/) - Modular system capabilities
- [YAML UI Examples](../../yaml/ui/) - UI component definitions in YAML
