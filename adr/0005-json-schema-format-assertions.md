# ADR-0005: JSON Schema format assertions — enforce the core interoperability formats

- **Status:** Accepted
- **Date:** 2026-09-11
- **Deciders:** GTS spec maintainers
- **Consulted:** aviator5
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

GTS Type Schemas and effective trait schemas use JSON Schema. JSON Schema permits implementations to treat `format` as annotation rather than assertion, so schemas that declare a standard format can produce different validation results across implementations.

The OP#6 and OP#13 conformance tests require invalid values for the common interchange formats to be rejected. The specification must make that requirement explicit, including whether it applies to both instance properties and effective trait values.

## Decision Drivers

- Interoperable validation results across GTS implementations.
- A small, explicit set of widely implemented JSON Schema formats.
- One shared rule for OP#6 instance validation and OP#13 effective trait validation.
- Preserve dialect-specific handling for formats outside the selected set.

## Considered Options

- Option 1 — Leave `format` annotation-only
- Option 2 — Assert every JSON Schema format
- Option 3 — Assert the core interchange formats *(chosen)*

### Option 1 — Leave `format` annotation-only

GTS would retain the JSON Schema default and allow implementations to ignore every `format` keyword during validation.

### Option 2 — Assert every JSON Schema format

GTS would require assertion for every format recognized by an implementation or JSON Schema dialect.

### Option 3 — Assert the core interchange formats

GTS requires OP#6 and OP#13 to assert `uuid`, `email`, `date-time`, `date`, `time`, `uri`, `hostname`, `ipv4`, `ipv6`, and `regex` when they constrain string values. This applies to instance properties and the effective trait values validated against the effective trait schema. The `regex` format follows its JSON Schema Draft-07 definition: a string value is valid when it is a regular expression that is valid according to the ECMA 262 regular expression dialect. Other format names retain their selected JSON Schema dialect's semantics.

## Decision Outcome

Chosen option: "Option 3", because it establishes portable behavior for the common formats covered by the conformance suite without requiring an open-ended implementation-specific format catalog.

### Implications

- §9.2 states the shared OP#6 and OP#13 requirement.
- OP#6 and OP#13 conformance tests cover valid and invalid values for each required format.
- Implementations must enable or provide assertion behavior for the listed formats.
- Other `format` values remain subject to selected JSON Schema dialect semantics.

## Pros and Cons of the Options

### Option 1 — Leave `format` annotation-only

- **+** Exactly follows the permissive JSON Schema default.
- **−** Allows conformance implementations to disagree on validation outcomes.

### Option 2 — Assert every JSON Schema format

- **+** Makes all recognized formats strict.
- **−** Creates an open-ended and dialect-dependent conformance obligation.

### Option 3 — Assert the core interchange formats

- **+** Provides portable behavior for common values used in GTS schemas and traits.
- **+** Keeps the required format set explicit and testable.
- **−** Implementations may still differ for formats outside the required set.

## More Information

The effective trait schema and effective traits object are defined in §9.7. OP#13 validates the latter against the former; therefore, this requirement applies to format constraints reached through the effective trait schema as well as directly declared constraints.
