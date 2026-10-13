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

### Identifier matching corpus

`id_pattern_corpus.py` holds the shared [README §10](../README.md#10-identifier-matching-and-pattern-coverage) vectors as plain data with explicit expected results. It includes every matching, coverage, and invalid-pattern table of §10 and the examples in its text, plus former OP#4 and `x-gts-pattern-ref` vectors:

- `MATCH_CASES` pair a pattern with a canonical candidate and state two results separately: point matching (`candidate ∈ M(pattern)`) and coverage (`M(candidate) ⊆ M(pattern)`). An unmatched candidate is its own coverage witness.
- `COVERAGE_CASES` pair a filter with a wildcard candidate; each uncovered row names a canonical witness selected by the candidate and not by the filter.
- `VALID_PATTERNS` and `INVALID_PATTERNS` cover syntax, spelling, length, and unsigned 32-bit version bounds.

Adapters use the corpus as follows:

- **OP#4** (`test_op4_id_match_pattern.py`): concrete candidates by point matching, pattern candidates by coverage, with witnesses checked in both directions. Valid pairs must report no error, so a non-match cannot pass because of a parse failure. Invalid strings, as pattern or candidate, return `match=false` and an error.
- **Entity references** (`test_x_gts_entity_ref.py`): each match row under both keywords, accepted iff the candidate matches and has the required kind. Covered pattern candidates are still rejected. Concrete Instance ID operands are schema errors under `x-gts-type-ref`. These run with `gts-ref-validation=none` in every dialect, without registering candidates.
- **`x-gts-pattern-ref`** (`test_x_gts_pattern_ref.py`): every row by coverage, including uncovered witnesses; `gts.*` checks the syntax lists.
- **Invalid operands:** every `INVALID_PATTERNS` string is a schema error as the operand of all three keywords. Local operand lists add only keyword-specific forms: pointers other than `/$id`, non-string JSON values, and the operand kind restriction.

`test_gts_id_pattern_syntax_unit.py` checks offline that every corpus string is spelled correctly, that match candidates and witnesses are canonical, that coverage candidates are wildcards, and that case IDs and vectors are unique. It also checks lengths at the empty-selection boundary. It does not compute matching or coverage.

### GTS identifier pattern constraint tests

`test_x_gts_pattern_ref.py` checks `x-gts-pattern-ref` from [README §9.6.2](../README.md#962-pattern-valued-fields-x-gts-pattern-ref), [§10](../README.md#10-identifier-matching-and-pattern-coverage), and [ADR-0007](../adr/0007-gts-pattern-ref.md) in all three supported dialects:

- **Syntax and coverage:** the shared corpus above. Valid patterns whose every completion exceeds 1024 characters select no identifier and are covered by any operand. Each uncovered case names a witness, which the value's own scope must accept and the operand reject. A small set checks that `not` inverts covered, uncovered, and malformed verdicts; invalid operands remain schema errors in registration, transient schema validation, and value validation after deferred registration.
- **Schema paths:** property and array schemas, local `$ref`, composition, literal data, and effective-leaf `/$id`.
- **Traits:** trait values given on the leaf, inherited from an ancestor, supplied by `default`, and supplied on abstract types, plus `/$id` in trait schemas.
- **Registry independence:** empty, valid, and invalid target states under every `gts-ref-validation` mode, including registration with validation. With unregistered operands and values, schema and instance validation succeed both before and after OP#7 relationship discovery. The tests do not assert which pattern-related relationships OP#7 reports.

Related conformance tests cover:

- **OP#8 and OP#12:** evolution and derivation, including composition, self-reference, narrowing and widening between first-segment `v1~` and `v1.*`, and pinning or omitting minors in an instance selector's type and instance segments. OP#8 composition cases permit `unknown` but reject incorrect definite verdicts.
- **OP#10:** version wildcard queries check the exact set of returned base types, derived types, and instances. A first-segment `v1.*` requires an explicit minor under major version 1; `v1~*` accepts omitted and explicit minors, while `v1.0~*` pins the minor to zero. Both chain-suffix patterns include the matching base types themselves.
- **Entity references:** see below; payload values are always concrete identifiers, never patterns.

### Entity reference tests

`test_x_gts_entity_ref.py` checks `x-gts-type-ref` and `x-gts-instance-ref` from [README §9.6.1](../README.md#961-entity-references-x-gts-type-ref--x-gts-instance-ref), [§9.6.3](../README.md#963-common-validation-rules), and [ADR-0008](../adr/0008-kind-specific-references.md) in all three supported dialects:

- **Operands:** concrete Type IDs, §10 wildcards, `/$id`, and the 1024-character boundary are valid for both keywords. Concrete and UUID-tailed Instance IDs are valid only for `x-gts-instance-ref`; under `x-gts-type-ref` they are schema errors. Invalid pattern strings from the shared corpus, other pointers, and non-strings are schema errors for both. Schema errors are checked on registration with validation, `POST /validate-json`, and after registration without validation (which may also reject early), at every schema location: properties, array items, unused definitions, inactive `anyOf` and `if`/`then` branches, `not`, and trait schemas. The removed `x-gts-ref` and an unknown `x-gts-*` keyword follow the same lifecycle. Keyword-shaped keys in literal data and property names are accepted.
- **Candidates:** detailed matching comes from the shared §10 corpus (see above), run with `gts-ref-validation=none`. Registered controls show that lookup replaces neither kind nor matching in any mode. A concrete Type ID operand is checked against registered, valid candidates: types and instances under it, including derived types, explicit minors, and UUID instances, and others outside it. Malformed values with a matching root and suffix are rejected. Concrete named and UUID Instance ID operands accept their registered target and reject a registered, valid instance outside their scope. The suite also covers string-only applicability, `anyOf`/`oneOf` unions, conjunction, `not`, and `const`.
- **Transient instances:** `POST /validate-json/{gts_type}` selects the type explicitly, while `POST /validate-json` infers it from the payload's `type` field. Both paths check candidate kind and matching, reject pattern and malformed candidates, allow absent optional references, and resolve inherited `/$id` against the selected leaf, including further derivation. Concrete targets are registered and valid to isolate structural checks from lookup policy. If registration without validation stores a schema with an invalid operand, both paths reject payloads with or without the reference property.
- **`/$id`:** selected-leaf resolution through `$ref` and inline `allOf`, further derivation, ancestor and sibling rejection, and no import through a chained `$id` alone.
- **Registry policies:** candidate lookup and validity per mode, wrong-kind rejection of registered targets, wildcard operands witnessed by an entity of the other kind, missing or invalid concrete operand targets, and abstract or final targets.
- **Traits:** leaf, inherited, default, abstract-type, and `/$id` trait values.

Structural cases on the registered-entity validation endpoints use `gts-ref-validation=none` so that registry lookup cannot cause or mask a verdict. The transient validation endpoints have no policy parameter; their structural instance cases use registered, valid targets and have the same expected results under every policy. Transient schema errors are paired with a valid control whose operand target is registered and valid.

`test_refimpl_x_gts_ref.py` covers each keyword on concrete fields: combinators, local and root references, tuple and `prefixItems` arrays, nullable references, wildcard families, and registry modes, including exact lookup of a minor-flexible match. OP#13 trait cases in `test_op13_schema_traits_validation.py` use `x-gts-instance-ref` for topic instances and `x-gts-type-ref` for referenced type chains. OP#8 and OP#12 cases cover equal, narrower, and broader kind-filtered scopes, kind swaps, unions, `not`, and `/$id` on each side.

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
- [x] **OP#4 - ID Pattern Matching**: Match concrete identifiers or candidate patterns using the §10 matching and coverage rules
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
