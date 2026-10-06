# Tests

This directory contains test cases for the GTS specification [reference implementation recommendations](../README.md#9-reference-implementation-recommendations). The test cases are implemented using Pytest and are designed to run against any web server implementing the GTS operations API.

## Architecture Rationale

### Why Tests Live in the Specification Repository

The tests are intentionally kept **alongside the specification** rather than in individual language implementations for several critical reasons:

1. **Single Source of Truth**: The specification defines the contract that all implementations must satisfy. By keeping tests here, we ensure that all language implementations (Python, Go, Rust, etc.) are validated against the exact same behavioral requirements.

2. **Implementation Independence**: Tests are written as black-box HTTP API tests, making them completely language-agnostic. Any implementation that exposes the required HTTP endpoints can be validated, regardless of the underlying technology stack.

3. **Specification Evolution**: When the GTS specification evolves, the tests evolve in lockstep. This prevents drift between what the spec defines and what implementations are tested against.

4. **Cross-Implementation Consistency**: All implementations must pass the same test suite, guaranteeing behavioral consistency across Python, Go, Rust, and future language bindings.

5. **Easier Onboarding**: New implementation authors can immediately validate their work against the canonical test suite without having to interpret or reimplement test logic.

### Why Implementations Are Separate

While tests live with the specification, the actual server implementations are maintained in separate repositories:

- [gts-python](https://github.com/globaltypesystem/gts-python) - Python implementation
- [gts-go](https://github.com/globaltypesystem/gts-go) - Go implementation
- [gts-rust](https://github.com/globaltypesystem/gts-rust) - Rust implementation

**Reasons for separation:**

1. **Language-Specific Tooling**: Each language has its own dependency management, build systems, and development workflows (pip/poetry for Python, go modules, cargo for Rust).

2. **Independent Release Cycles**: Implementations can release bug fixes, performance improvements, and language-specific features without requiring specification changes.

3. **Community Ownership**: Different teams or maintainers can own different language implementations while all adhering to the same specification.

4. **Reduced Coupling**: Separating implementations prevents language-specific concerns from polluting the specification repository.

### Testing Approach

The test suite validates implementations through a standardized HTTP API. Each implementation must:

- Expose endpoints defined in [openapi.json](openapi.json)
- Run on port 8000 (configurable via `GTS_BASE_URL`)
- Implement all required GTS operations (ID validation, parsing, schema validation, etc.)

This approach provides:
- **Technology neutrality**: Tests use only HTTP and JSON, no language-specific dependencies
- **Portability**: Tests can run in any environment with Python and network access
- **Simplicity**: No complex test harnesses or language interop required

### Server behaviour prerequisites

Some test cases assert behaviour that the specification leaves implementation-defined. Servers under test must satisfy these prerequisites for the suite to pass:

- **Immutable registry** (`OP#6` resubmission cases, e.g. `TestCaseOp6InstanceResubmission` / `TestCaseOp6TypeResubmission`): registration is treated as immutable per identifier. Resubmitting an entity with **identical** content under an existing ID must succeed (`200`), while submitting **changed** content under an already-registered ID must be rejected with `409 Conflict`. Spec §6 does not mandate a mutability policy, so implementations that permit in-place updates will not satisfy these tests.
- **Non-mutating validation** (`TestCaseOp13_TraitRef_RevalidationPreservesStoredSchema`): validation does not register, replace, or remove entities. An entity accepted without validation remains stored if later validation rejects it; removal is an explicit client operation. A failed registration-with-validation must leave the registry as it was before the request.

## Running the tests

### With Docker (recommended)

A pre-built image is published to the GitHub Container Registry on every release. The image tag tracks the specification version: `vMAJOR.MINOR` matches the spec, and the `PATCH` segment increments on test-suite changes (e.g. `v0.11.3` runs against spec `0.11`).

Pick the tag that fits your use case:

- `vX.Y.Z` — exact release (e.g. `v0.11.3`). Recommended for CI / reproducible runs.
- `vX.Y` — rolling tag for the freshest patch of a given spec version (e.g. `v0.11`). Recommended for interactive use when you want to validate against a specific spec version.

> There is no `latest` tag. Multiple spec versions can be maintained in parallel (e.g. a `v0.9.x` backport patch while main is at `0.11`), and a single floating `latest` would not have an unambiguous meaning. Always pin to either `vX.Y.Z` or `vX.Y`.

```bash
# Start your server on the host (port 8000 in this example)
<your-server-start-command>

# Run the test suite from the published image (Mac/Docker Desktop)
docker run --rm ghcr.io/globaltypesystem/gts-spec-tests:v0.11 \
    --gts-base-url http://host.docker.internal:8000

# Linux hosts (host.docker.internal is not built-in)
docker run --rm --add-host=host.docker.internal:host-gateway \
    ghcr.io/globaltypesystem/gts-spec-tests:v0.11 \
    --gts-base-url http://host.docker.internal:8000

# Pin to an exact release for reproducible CI runs
docker run --rm ghcr.io/globaltypesystem/gts-spec-tests:v0.11.3 \
    --gts-base-url http://host.docker.internal:8000

# Run a specific test file or pytest selector
docker run --rm ghcr.io/globaltypesystem/gts-spec-tests:v0.11 \
    --gts-base-url http://host.docker.internal:8000 \
    test_op1_id_validation.py
```

To rebuild the image locally while iterating on tests:

```bash
docker build -t gts-spec-tests -f tests/Dockerfile tests
docker run --rm gts-spec-tests --gts-base-url http://host.docker.internal:8000
```

### With Python

```bash
# Start your server on 8000 port
<your-server-start-command>

# Install test dependencies (recommended)
python -m pip install -r ./tests/requirements.txt

# Run all the tests
pytest .

# Run a specific test case group
pytest op1_id_validation_test.py

# override server URL using GTS_BASE_URL environment variable
GTS_BASE_URL=http://127.0.0.1:8001 pytest

# or set it persistently
export GTS_BASE_URL=http://127.0.0.1:8001
pytest
```

### Regular-expression tests

`test_regex_validation.py` checks the bounded GTS regex profile (a closed subset of ECMA-262 `u` and RE2), reference matching, declared deviations, and execution safety from [README §11.0.1](../README.md#1101-regular-expression-execution-safety) and [ADR-0006](../adr/0006-safe-regexp-profile.md):

- **Support:** accept in-profile expressions; reject malformed, engine-specific, and excluded syntax, including ambiguous spellings. Check the limits and adjacent values: 4096 expanded code points (including astral literals), 32 nested groups, and repetition counts/products of 1000. Upper counts multiply; zero counts and `*` contribute one. Unsupported patterns cause schema errors; unsupported regex-valued strings cause format violations invertible by `not`.
- **Reference matching:** require RE2 results, including `.` matching CR, U+2028, and U+2029, ASCII shorthands inside and outside classes, and code-point matching for astral characters and `\xHH`. Paths include direct, referenced, and inherited `pattern`; stored-instance `/validate-instance` and `/validate-entity`; `propertyNames`; `patternProperties`; `additionalProperties` and `unevaluatedProperties` classification; and traits. Every path must satisfy the expected support and matching results.
- **Declared deviations:** test `\d`, `\w`, and `\s`, including classes and Unicode word-set probes (marks, Join_Control, non-ASCII digits), against the declared behavior; undeclared constructs use the reference.
- **Safety and failures:** check unsupported syntax and bounds in every schema position at registration and explicit validation after deferred registration. Literal data and unknown dialect keywords are excluded unless referenced as schemas. Operational failures must explicitly fail validation, including under `not` and during property classification.

| Variable | Default | Purpose |
|----------|---------|---------|
| `GTS_TEST_REGEX_DECLARED_BEHAVIOR` | empty | JSON object: `digit`, `word`, and `space` each accept `unicode` or `reference`; omitted keys use the reference. For Rust `regex` defaults, set `{"digit": "unicode", "word": "unicode", "space": "unicode"}`. RE2, Go, RE2/J, and RE2JS need no declaration. |
| `GTS_TEST_REGEX_STRESS_SECONDS` | `2` | Response time limit for stress cases. |

Stress workloads use ambiguous in-profile expressions: ~50,000-character strings, 500-character counted-repetition matches, arrays of 1,000 strings of 65 characters, and 32 property names of 65–96 characters. Positive cases require successful validation within the response limit. These workloads define the test environment, not GTS minimum capacity; tighter server limits may fail positive tests with explicit errors.

Open questions (not asserted):

- Must instance validation reject unsupported expressions in inactive branches after deferred registration? Explicit schema validation must reject them and is tested.
- CI still compiles examples with Ajv only; a GTS profile checker remains to be added.

Limitations:

- The API's `ok` and error string cannot distinguish a mismatch from an operational failure. Complementary verdicts for a schema and its negation detect persistent failures under stable conditions, but independent requests cannot reliably classify transient failures. Stress checks allow either rejection or explicit error where specified.
- Resource exhaustion needs local tests, such as fault injection; it cannot be triggered portably.
- Stress timing detects regressions, not complexity guarantees. Client timeouts do not stop server work.
- Offline checks use fake engines (`test_regex_validation_unit.py`, `pytest tests -m unit`, run in CI), not a profile checker or RE2 implementation.

## Generating reusable examples

`generate_examples.py` runs the conformance tests against a GTS server and records the JSON entities submitted to the server. It writes only entities that the server subsequently reports as valid or invalid, preserving the server's actual request payloads rather than recreating them from test source code.

Start a compatible GTS server, then run the generator with the same Python environment used for the test suite:

```bash
python tests/generate_examples.py
```

Use `--gts-base-url` to specify the GTS server URL, `--output` to select another destination, or provide one or more `test_*.py` paths to generate examples from a subset of the suite:

```bash
python tests/generate_examples.py \
    --gts-base-url http://127.0.0.1:8000 \
    --output ./generated-examples \
    tests/test_op6_schema_validation.py
```

By default, the generator writes to `gts-test-examples/` with this layout:

```
gts-test-examples/
  valid/
    instances/*.json
    types/*.schema.json
  invalid/
    instances/*.jsonc
    types/*.schema.jsonc
```

Invalid JSONC files begin with `// Invalid:` comments containing the validation error returned by the server. Valid examples remain strict JSON so they can be consumed directly by JSON parsers.

The generated corpus is useful beyond end-to-end testing. Static validators can use the valid and invalid pairs as regression fixtures, IDE plugins can surface the embedded invalid-example reasons while editing schemas or instances, and documentation, language bindings, and editor integrations can use the real request payloads as example data without requiring a running registry.

## Implemented test cases

- [x] **OP#1 - ID Validation**: Verify identifier syntax using regex patterns
- [x] **OP#2 - ID Extraction**: Fetch identifiers from JSON objects or JSON Schema documents
- [x] **OP#3 - ID Parsing**: Decompose identifiers into constituent parts (vendor, package, namespace, type, version, etc.)
- [x] **OP#4 - ID Pattern Matching**: Match identifiers against patterns containing wildcards
- [x] **OP#5 - ID to UUID Mapping**: Generate deterministic UUIDs from GTS identifiers
- [x] **OP#6 - Schema Validation**: Validate object instances against their corresponding schemas
- [x] **OP#7 - Relationship Resolution**: Load all schemas and instances, resolve inter-dependencies, and detect broken references
- [x] **OP#8 - Compatibility Checking**: Verify that schemas with different MINOR versions are compatible
- [x] **OP#8.1 - Backward compatibility checking**
- [x] **OP#8.2 - Forward compatibility checking**
- [x] **OP#8.3 - Full compatibility checking**
- [x] **OP#9 - Version Casting**: Transform instances between compatible MINOR versions
- [x] **OP#10 - Query Execution**: Filter identifier collections using the GTS query language
- [x] **OP#11 - Attribute Access**: Retrieve property values and metadata using the attribute selector (`@`)
