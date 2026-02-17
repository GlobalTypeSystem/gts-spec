# Contributing to GTS Specification

Thank you for your interest in contributing to the Global Type System (GTS) Specification! This document provides guidelines and information for contributors.

## Quick Start

### Prerequisites

- **Git** for version control
- **JSON Schema validator** (optional, for testing schema examples)
- **Python 3.8+** (optional, for running reference implementations)
- **Your favorite editor** (VS Code with JSON Schema support recommended)

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd gts-spec

# Optional: Install Python dependencies for reference implementations
pip install jsonschema

# Optional: Install JSON Schema validator
npm install -g ajv-cli
```

### Repository Layout

```
gts-spec/
├── README.md                 # Main specification document
├── CONTRIBUTING.md           # This file
├── LICENSE                   # License information
└── examples/                 # Example schemas and instances
    ├── events/               # Event-related examples
    │   ├── schemas/          # JSON Schema definitions
    │   └── instances/        # JSON instance examples
    └── ...                   # Other domain examples
```

## Development Workflow

### 1. Create a Feature Branch or fork the repository

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-event-examples`
- `fix/schema-validation-error`
- `docs/clarify-chaining-rules`
- `spec/minor-version-compatibility`

### 2. Make Your Changes

Follow the specification standards and patterns described below.

### 3. Validate Your Changes

```bash
# Validate all schemas in a directory
ajv compile --strict=false -s "examples/events/schemas/*.schema.json"

# Run Python reference implementation tests (if available)
python -m pytest tests/
```

### 4. Commit Changes

Follow a structured commit message format:

```text
<type>(<module>): <description>
```

- `<type>`: change category (see table below)
- `<module>` (optional): the area touched (e.g., spec, examples, schemas)
- `<description>`: concise, imperative summary

Accepted commit types:

| Type       | Meaning                                                     |
|------------|-------------------------------------------------------------|
| spec       | Specification changes or clarifications                     |
| fix        | Bug fixes in schemas or examples                            |
| docs       | Documentation updates                                       |
| examples   | Adding or updating example schemas/instances                |
| test       | Adding or modifying validation tests                        |
| style      | Formatting changes (whitespace, JSON formatting, etc.)      |
| chore      | Misc tasks (tooling, scripts)                               |
| breaking   | Backward incompatible specification changes                 |

Examples:

```text
spec(versioning): clarify minor version compatibility rules
fix(schemas): correct `$id` pattern in event schema
examples(idp): add contact_created event instance
test(validation): add schema validation tests
```

Best practices:

- Keep the title concise (ideally ≤ 50 chars)
- Use imperative mood (e.g., "Fix schema", not "Fixed schema")
- Make commits atomic (one logical change per commit)
- Add details in the body when necessary (what/why, not how)
- For breaking changes, either use `spec!:` or include a `BREAKING CHANGE:` footer

Specification development guidelines:

- Follow GTS identifier format rules strictly
- Ensure all schemas use correct `$id` values
- Validate schemas against JSON Schema Draft 7 or later
- Include both type definitions (schemas) and instance examples
- Document any deviations or implementation-specific choices
