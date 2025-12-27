# UI Component Examples (YAML)

This directory contains GTS examples for user interface components defined in YAML format.

## Overview

These examples demonstrate:
- **Base UI item type**: Common properties for all UI elements
- **Derived UI types**: Specialized components (menu items, data grids)
- **YAML format**: Human-readable schema and instance definitions
- **Type inheritance**: How UI components extend base properties

## Schema Definitions (YAML)

YAML schemas are JSON Schema definitions written in YAML format for better readability and maintainability.

### Base Type

- **`gts.x.ui.core.item.v1~.schema.yaml`**
  - Base UI item type with common properties
  - Properties: `gtsId`, `id`, `type`, `label`, `description`, `visible`, `enabled`, `position`, `permissions`, `style`, `metadata`

### Derived Types

- **`gts.x.ui.core.item.v1~x.ui.components.menu_item.v1~.schema.yaml`**
  - Menu item component for navigation menus
  - Adds: `navigation` (target, type, params), `icon`, `badge`, `parentMenuId`, `children`, `shortcut`
  - Use cases: Main navigation, sidebars, dropdown menus, context menus

- **`gts.x.ui.core.item.v1~x.ui.components.grid.v1~.schema.yaml`**
  - Data grid component for tabular data display
  - Adds: `columns` (definitions with sorting/filtering), `dataSource` (API config), `pagination`, `selection`, `actions`
  - Use cases: User lists, data tables, reports, admin panels

## Instance Examples (YAML)

### Menu Items

- **`main_dashboard.yaml`**
  - Dashboard menu item with icon and navigation
  - Target: `/dashboard` route
  - Permission: `view:dashboard`

- **`user_settings.yaml`**
  - Settings menu item with badge notification
  - Keyboard shortcut: `Ctrl+,`
  - Shows count badge and help URL

### Data Grid

- **`users_list.yaml`**
  - Users list grid with 6 columns
  - Features: sorting, filtering, pagination (25 per page)
  - Multi-select with row actions (edit, deactivate, reset password)
  - Data source: REST API endpoint

## GTS Identifier Pattern

UI components follow the inheritance chain:

```
gts.x.ui.core.item.v1~<vendor>.<package>.components.<component_type>.v1~
```

Examples:
- `gts.x.ui.core.item.v1~x.ui.components.menu_item.v1~`
- `gts.x.ui.core.item.v1~x.ui.components.grid.v1~`

## YAML vs JSON

YAML provides several advantages for configuration and schemas:
- More human-readable (no quotes, less punctuation)
- Supports comments
- Better for version control (cleaner diffs)
- 1:1 conversion to/from JSON

Convert between formats:

```bash
# YAML to JSON
python -c "import yaml, json, sys; print(json.dumps(yaml.safe_load(sys.stdin), indent=2))" < file.yaml > file.json

# JSON to YAML
python -c "import yaml, json, sys; print(yaml.dump(json.load(sys.stdin), default_flow_style=False))" < file.json > file.yaml
```

## Use Cases

These examples demonstrate how GTS enables:

1. **Dynamic UI generation**: Render UI components from GTS definitions stored in a database
2. **Permission-based UI**: Control visibility/access based on GTS patterns (e.g., `gts.x.ui.core.item.v1~*`)
3. **Multi-tenant customization**: Different vendors can extend base UI types with custom properties
4. **Configuration as code**: Define UI layout and behavior in version-controlled YAML files

## Validation

Validate YAML instances against schemas:

```bash
# Using yajsv (Yet Another JSON Schema Validator with YAML support)
go install github.com/neilpa/yajsv@latest
yajsv -s schemas/gts.x.ui.core.item.v1~x.ui.components.menu_item.v1~.schema.yaml \
      instances/gts.x.ui.core.item.v1~x.ui.components.menu_item.v1~main_dashboard.yaml
```

Alternatively, convert to JSON first and use ajv:

```bash
# Install ajv-cli
npm install -g ajv-cli

# Convert YAML to JSON and validate
cat instances/gts.x.ui.core.item.v1~x.ui.components.menu_item.v1~main_dashboard.yaml | python -c "import yaml, json, sys; print(json.dumps(yaml.safe_load(sys.stdin)))" | \
ajv validate -s schemas/gts.x.ui.core.item.v1~x.ui.components.menu_item.v1~.schema.json -d -
```

## Extending UI Components

To add a new UI component type:

1. Create a schema that extends `gts.x.ui.core.item.v1~`
2. Use `allOf` to inherit base properties
3. Add component-specific properties
4. Follow GTS naming: `gts.x.ui.core.item.v1~<vendor>.components.<type>.v<version>~`

Example component types to add:
- Form component with field definitions
- Button with action handlers
- Modal/dialog with content
- Chart/visualization component
- File upload component

## Related Examples

- [Events Examples](../../events/) - Event-driven architecture with GTS
- [TypeSpec VM Examples](../../typespec/vms/) - VM types in TypeSpec format
- [Modules Examples](../../modules/) - Modular system capabilities
