# Contributing to GTS Specification

Thank you for your interest in contributing to the Global Type System (GTS) Specification! This document provides guidelines and information for contributors.

## Quick Start

### Prerequisites

- **Git** for version control
- **Node.js 20+ and `ajv-cli`** (optional, for validating JSON Schema examples as CI does)
- **Python 3.9–3.14** (optional, for working on the conformance test suite)
- **Docker** (optional, and recommended for running the conformance test suite)
- **Your favorite editor** (VS Code with JSON Schema support recommended)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/GlobalTypeSystem/gts-spec.git
cd gts-spec

# Optional: install the JSON Schema validator used by CI
npm install -g ajv-cli
```

The conformance tests run against an external GTS implementation over HTTP; this repository does not contain a reference implementation. See [`tests/README.md`](tests/README.md) for Docker and local Python setup.

### Repository Layout

```
gts-spec/
├── README.md                 # Normative specification
├── CONTRIBUTING.md           # This file
├── LICENSE                   # License
├── NOTICE                    # Attribution notices
├── adr/                      # Architecture Decision Records (+ template.md)
├── examples/                 # GTS Types and Instances in JSON, YAML, and TypeSpec
├── tests/                    # Implementation-independent HTTP conformance tests
└── .github/workflows/        # CI and release workflows
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

#### Specification changes require an ADR

Any proposal that adds normative behavior to the specification or intentionally changes existing normative behavior **MUST go through the Architecture Decision Record (ADR) process**. Start by copying the project-adapted MADR [`ADR template`](adr/template.md) to the next sequentially numbered file under [`adr/`](adr/) and fill in all applicable sections. The specification, tests, and examples must reference or implement the decision where applicable.

Open the pull request with the ADR already at **`Status: Accepted`** — the decision is what is under review, so accepting the ADR *is* merging the pull request. There is no separate approval step and no `Proposed` state in the repository: an ADR on `main` is accepted by definition. A decision that is later replaced keeps its file and moves to `Status: Superseded`, with `Superseded by` pointing at the ADR that replaces it (and that ADR's `Supersedes` pointing back). The ADR may be reviewed in its own pull request or together with the resulting specification change; either way it must not be merged before the reviewers agree on the decision itself.

A confirmed bug fix does not require a new ADR when it only restores behavior already established by the specification or an accepted ADR. If fixing the issue requires choosing new semantics, it is a specification change and therefore requires an ADR.

### 3. Validate Your Changes

```bash
# Validate the JSON Schema examples covered by CI
ajv compile -s "examples/*/types/*.schema.json" --strict=false

# Run the conformance tests against a GTS server already listening on port 8000
python -m pytest tests/ --gts-base-url http://127.0.0.1:8000
```

Run the checks relevant to the files you changed. JSONC, YAML, TypeSpec, nested example directories, and unresolved `gts://` references may require their own format-aware validation in addition to the CI command above. For test-suite setup and targeted test invocations, follow [`tests/README.md`](tests/README.md).

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
| examples   | Adding or updating example schema representations and instances |
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
- Declare the intended JSON Schema dialect with `$schema` and use keywords valid for that dialect; GTS is dialect-agnostic, while repository examples generally use Draft-07 for interoperability
- Include both GTS Type Schemas (the canonical JSON definitions of types) and GTS Instance examples
- Keep normative specification changes, conformance tests, and examples aligned
- Document any deviations or implementation-specific choices

## Releases

The specification version is declared in `README.md` via a machine-readable marker on the first line:

```html
<!-- gts-spec-version: X.Y -->
```

This marker is the canonical source of truth and is parsed by CI. The visible `> **VERSION**: ...` line below it is for human readers only and may be reworded freely, but its `X.Y` value MUST match the marker. When bumping the spec version, update both lines in the same change.

A versioned Docker image of the conformance test suite is published to GHCR on every git tag matching `vX.Y.Z`, where:

- `X.Y` MUST match the spec version declared in `README.md`. The release workflow enforces this and will fail the build on mismatch.
- `Z` increments independently for changes to the test suite itself (additions, fixes, refactors) within the same spec version.

When the specification moves to the next minor version (e.g. `0.11` → `0.12`), the README version line is updated in the same change, and the next release tag starts at `vX.Y.0`.

### Cutting a release (maintainers only)

Releases are produced from `github.com/GlobalTypeSystem/gts-spec`. The workflow is restricted to that repository; pushing a tag from a fork has no effect.

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The [`Release Tests Image`](.github/workflows/release-tests-image.yml) workflow:

1. Verifies the tag's `major.minor` matches the spec version in `README.md`.
2. Builds the test runner image for `linux/amd64` and `linux/arm64`.
3. Pushes it to `ghcr.io/globaltypesystem/gts-spec-tests` with two tags: the exact release `vX.Y.Z` and the rolling per-spec-version `vX.Y`. No floating `latest` tag is published — see `tests/README.md` for the rationale and consumer-side tag selection guidance.
4. Creates a GitHub Release with auto-generated notes.
