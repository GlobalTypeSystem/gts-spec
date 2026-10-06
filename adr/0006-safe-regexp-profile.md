# ADR-0006: Safe regular expressions — a common syntax profile with declared matching differences

- **Status:** Accepted <!-- Accepted on merge, per CONTRIBUTING.md. -->
- **Date:** 2026-10-04
- **Deciders:** GTS spec maintainers
- **Consulted:** aviator5
- **Supersedes:** The full ECMA-262 requirement in §11.0 and the `regex` format semantics in [ADR-0005](0005-json-schema-format-assertions.md); its format-assertion requirement is unchanged.
- **Superseded by:** —

## Context and Problem Statement

GTS schemas and payloads may be untrusted. GTS 0.14 requires full ECMA-262 support, including constructs unavailable in engines such as RE2, Go `regexp`, and Rust `regex`. These engines also differ in syntax and matching details. [JSON Schema recommends ECMA-262 and a portable subset](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.4.3), without prescribing a matching algorithm.

Which regex constructs should GTS support, which matching differences should it allow, and how should implementations prevent ReDoS? This decision covers `pattern`, `patternProperties`, and `format: "regex"`, including effective trait validation and property classification for `additionalProperties` and `unevaluatedProperties`.

## Decision Drivers

- A common expression syntax across GTS implementations.
- Existing safe engines usable across runtimes, including browsers.
- Explicit, limited differences in matching results.
- Bounded matching and compilation costs for each expression.
- Consistent support checks and error handling across every regex path.

## Considered Options

- Option 1 — Retain ECMA-262 with whole-validation resource budgets
- Option 2 — Mandatory RE2-compatible baseline with safe execution
- Option 3 — Safe engines with a common syntax profile, ECMA-262 reference matching, and permitted differences
- Option 4 — Safe engines with a common syntax profile, RE2 reference matching, and permitted differences *(chosen)*
- Option 5 — Safe engines with implementation-defined syntax and matching semantics

All options require correct error handling. Options 2–5 additionally require linear Boolean search for a fixed expression. Options 2–4 can use the same construct inventory; their differences concern matching rules and extensions.

### Option 1 — Retain ECMA-262 with whole-validation resource budgets

Keep the full GTS 0.14 syntax and matching contract. Bound total work using an enforceable deadline or shared budget across all regex evaluations. Linear matching is not required; per-match limits alone are insufficient.

### Option 2 — Mandatory RE2-compatible baseline with safe execution

Select a mandatory set from the [RE2 syntax reference](https://github.com/google/re2/wiki/Syntax), potentially the same constructs as Options 3 and 4. Within its bounds, all implementations must support those expressions and reproduce the Boolean results of a specified RE2 version and configuration. Extensions may differ but must not alter baseline behavior. Using the C++ RE2 library or adopting the full RE2 syntax is not required.

### Option 3 — Safe engines with a common syntax profile, ECMA-262 reference matching, and permitted differences

Define a closed syntax subset accepted by both ECMA-262 `u` and RE2; expressions outside the profile are rejected. ECMA-262 `u` defines matching, except for deviations explicitly allowed by GTS. Each implementation declares its behavior within those exceptions and executes every expression on a safe engine. RE2-family engines differ from the reference for `.` and `\s`, so they need adaptation or listed deviations for these constructs.

### Option 4 — Safe engines with a common syntax profile, RE2 reference matching, and permitted differences

Use the same closed syntax profile, declarations, and safe execution as Option 3, but with RE2 semantics, written out by GTS for the profile, as the matching reference. Unlike Option 2, the syntax is closed, and a listed deviation may replace an RE2 result.

### Option 5 — Safe engines with implementation-defined syntax and matching semantics

Require safe execution, but let each implementation define syntax and matching through its engine, version, options, and support limits. GTS provides no common expression language.

## Decision Outcome

Chosen option: **Option 4**, because it gives schema authors a common syntax, matches the native results of RE2-family engines without adaptation, and allows other safe engines, such as Rust `regex`, to differ in specified details. GTS libraries and services that validate the same stored schemas with the same engine, configuration, and Unicode version then get the same results. GTS maintains the profile and allowed deviations; each implementation enforces them and declares its behavior.

### Requirements

- **Common syntax:** define one fixed set of constructs accepted by both ECMA-262 `u` and RE2, with common support bounds. This makes expression syntax portable between implementations.
- **Declared matching differences:** use RE2 semantics, as defined for the profile, as the baseline. GTS lists the allowed deviations, and implementations declare which permitted behavior they use. This makes differences explicit and testable.
- **Safe matching:** require linear Boolean search for a fixed expression, including every fallback. This prevents catastrophic backtracking during matching; the syntax subset alone does not.
- **Consistent enforcement:** apply the same policy to every regex path, including traits, format checks, property classification, and generated validators. This prevents a path from bypassing the rules.
- **Explicit failures:** distinguish invalid expressions and ordinary non-matches from operational errors. An exhausted limit or engine abort must fail the validation, never turn into success through `not` or a skipped constraint.

### Implications

- GTS must maintain a profile grammar, common support bounds, and a closed list of allowed matching deviations. Implementations need a profile check; compiling with an engine that accepts a broader language is insufficient.
- The requirements above define the chosen approach. The supported constructs, the matching reference, the permitted deviations, and the common support bounds are defined below.
- The matching reference departs from the ECMA-262 dialect that JSON Schema recommends: `.` also matches CR, U+2028, and U+2029, and `\s` covers only five ASCII characters. Authors who need ECMA-262 results write explicit classes.
- The change replaces GTS 0.14's full ECMA-262 requirement and makes `format: "regex"` check the GTS profile. It is a breaking change targeted for GTS 0.15. ADR-0005's format-assertion requirement and other formats remain unchanged.
- [README §11.0.1](../README.md#1101-regular-expression-execution-safety) records the chosen contract. Before release, align the examples and conformance suite, and check existing expressions for compatibility.
- Expressions within the agreed bounds must be supported across implementations, but permitted deviations can change instance and trait validity. Uniform results for entire validations are not guaranteed, including because of resource failures and reference resolution.

## Pros and Cons of the Options

### Option 1 — Retain ECMA-262 with whole-validation resource budgets

- **+** Preserves existing expression syntax and matching results when evaluation completes.
- **−** Requires full-language support and enforceable interruption or work accounting on every path; short inputs can still exhaust the budget.

### Option 2 — Mandatory RE2-compatible baseline with safe execution

- **+** Provides common syntax and results within a baseline derived from an existing engine.
- **−** Requires bindings or adaptation where native engines differ. RE2 results can differ from ECMA-262 even for shared syntax; adopting additional RE2 constructs can also reduce syntax compatibility.

### Option 3 — Safe engines with a common syntax profile, ECMA-262 reference matching, and permitted differences

- **+** Provides portable syntax with the ECMA-262 `u` results that JSON Schema recommends, while accommodating specific behaviors of other engines.
- **−** Requires a profile checker and maintained exception list; permitted differences can change validation results. RE2-family engines (RE2, Go, RE2/J, RE2JS) differ for `.` and `\s`: either every such implementation adapts its engine, or their native results become listed deviations.

### Option 4 — Safe engines with a common syntax profile, RE2 reference matching, and permitted differences

- **+** Provides portable syntax and the native results of RE2-family engines while accommodating specific behaviors of other engines.
- **−** Requires a profile checker and maintained exception list; permitted differences can change validation results. The reference differs from ECMA-262 for `.` and `\s`.

### Option 5 — Safe engines with implementation-defined syntax and matching semantics

- **+** Requires no GTS syntax checker or semantic adapter.
- **−** The same expression may be rejected by another implementation or produce different results; syntax portability is not guaranteed.

## More Information

### Common syntax profile

The source expression must belong to a **closed subset of both ECMA-262 `u` syntax and RE2 syntax**, defined by the constructs and rules below. Membership is checked after JSON string decoding. Every implementation must support expressions within the profile's common bounds, given adequate operational resources. Engine-specific extensions are rejected.

An existing parser or shared checker may enforce the profile. Successful compilation by an engine accepting a broader language is insufficient. RE2's [syntax reference](https://github.com/google/re2/wiki/Syntax) informs the design, and RE2 semantics, as written out in [Matching rules and declarations](#matching-rules-and-declarations), are the matching reference; no particular library or binding is required.

#### Supported constructs

The profile consists of these constructs, combined by concatenation, alternation, grouping, and repetition, under the spelling rules and within the [common support bounds](#common-support-bounds). This table records the decision; [README §11.0.1](../README.md#1101-regular-expression-execution-safety) holds the normative list and the spelling rules. Anything else is outside the profile. Examples show decoded regex source, not JSON string literals.

| Construct | Forms |
|-----------|-------|
| Literals and concatenation | Outside a class, any code point except the syntax characters `^ $ \ . * + ? ( ) [ ] { } \|`, including Unicode literals. |
| Escaped metacharacters | `\` followed by a syntax character or `/`, such as `\.`, `\*`, and `\\`; no other identity escapes. |
| Character escapes | `\n`, `\r`, `\t`, `\f`, `\v`, `\xHH`. |
| Simple classes | `[abc]`, `[a-z]`, `[^abc]`, containing ranges, character escapes, escaped metacharacters, `\-`, shorthand classes, and literal code points other than `\`, `[`, and `]`, so `[a^$.*+?(){}\|]` lists punctuation literally. A leading `^` negates; `-` follows the spelling rules. |
| Groups and alternation | `(…)`, `(?:…)`, `a\|b`. Captured values are not exposed by GTS validation. |
| Repetition | `*`, `+`, `?`, `{n}`, `{n,}`, `{n,m}` with decimal `n ≤ m`, and their lazy forms with a `?` suffix. |
| Anchors and wildcard | `^`, `$`, `.`. |
| Shorthand classes | `\d`, `\D`, `\w`, `\W`, `\s`, `\S`. |
| Empty expression | Matches an empty substring; unanchored search succeeds on any supported string. |

The initial profile excludes lookaround, backreferences, atomic groups, possessive quantifiers, named groups, octal escapes, nested classes, class set operations, POSIX classes, Unicode properties, inline flags, word boundaries, and additional regex escapes such as `\A`, `\z`, `\Q…\E`, and `\uXXXX`. JSON `"\u0041"` decodes to the permitted literal `A`; JSON `"\\u0041"` decodes to the excluded regex escape `\u0041`.

#### Spelling rules

Spellings that ECMA-262 `u`, RE2, and Rust `regex` read differently, or that only some of them accept, are outside the profile. For example, RE2 reads `a{01}` as literal text, and Rust `regex` reads `[!--0]` as a set difference. [README §11.0.1](../README.md#1101-regular-expression-execution-safety) lists the rules.

#### Common support bounds

An expression is supported only within these bounds; exceeding any of them makes it unsupported, like syntax outside the profile:

| Bound | Limit |
|-------|-------|
| Expanded length | At most 4096 code points. |
| Group nesting | At most 32 nested groups. |
| Repetition count | Every `n` and `m` in `{n}`, `{n,}`, `{n,m}` at most 1000. |
| Nested repetition | Along every nesting path, the product of the counted-repetition factors at most 1000. |

The **expanded length** is the length of the expression after each counted repetition is replaced by copies of its operand: `X{n,m}` counts as its quantifier spelling plus `max(m, 1)` copies of `X`, `X{n}` as its spelling plus `max(n, 1)` copies, and `X{n,}` as its spelling plus `n + 1` copies, applied to nested repetitions as well. All other syntax, including `*`, `+`, `?`, lazy suffixes, groups, alternation, escapes, and class contents, counts by its spelling. Since every factor is at least one, the expanded length is never shorter than the source.

For the nested-repetition product, `X{n,m}` and `X{n}` contribute their upper count, `X{n,}` its lower count, a zero count contributes one, and `*`, `+`, `?` contribute one. For example, `a{1000}` (expanded length 1006) is supported, `(?:a{1000}){2}` exceeds the product, `(?:ab){1000}` (6006) exceeds the expanded length, and 4096 literal characters are supported.

These bounds keep compiled programs small for RE2, Go `regexp`, and Rust `regex`; Go and RE2 themselves reject repetition counts and nested products above 1000. The assessed Rust `regex` parser limits the nesting depth of the syntax tree to 250 by default, counting repetitions, alternations, concatenations, and classes as well as groups; one group level can take four of them, as in `(a|aX)*`, so 32 groups keep every expression of the current grammar within that limit. Revisit this bound if the grammar admits nested classes or stacked quantifiers. The expanded length is a conservative syntactic measure, not a compiled size: with the `word: unicode` or `space: unicode` deviation, Rust needs a larger compiled-size limit than its default for repeated shorthands near the bound.

Implementations must not silently shrink mandatory support through stricter local syntax limits.

### Matching rules and declarations

Matching follows the RE2 semantics defined here for the profile: unanchored search, case-sensitive matching, multiline and dot-all off, matching by Unicode code point. This defines reference behavior, not a requirement to use the RE2 library.

| Construct | Reference behavior |
|-----------|--------------------|
| `.` | Any code point except LF (U+000A). |
| `\s`, `\S` | Exactly U+0009, U+000A, U+000C, U+000D, and U+0020, and the complement. |
| `\d`, `\D` | `[0-9]` and the complement. |
| `\w`, `\W` | `[0-9A-Za-z_]` and the complement. |
| `^`, `$` | Start and end of the input only; `$` does not match before a final LF. |

The shorthand definitions also apply inside classes, including negated classes. RE2, Go `regexp`, RE2/J, and RE2JS give these results in their default configurations. ECMA-262 `u` without `i`, `m`, or `s` gives the same results within the profile except for `.`, which ECMA-262 also stops at CR, U+2028, and U+2029, and `\s`, which ECMA-262 defines as its WhiteSpace and LineTerminator sets. Authors who need those results write explicit classes, such as a negated class of LF, CR, and the literal characters U+2028 and U+2029. Strings with unpaired surrogates are not valid GTS input, as in I-JSON (RFC 7493), so GTS defines no results for them.

There are two levels of declaration:

1. **GTS specifies a closed list of allowed deviations and the permitted behaviors for each.** All other behavior follows the reference semantics.
2. **Each implementation declares which permitted behavior it uses**, together with its engine, version, configuration, and relevant Unicode version. The declared behavior must be consistent across all evaluation paths. Changes affecting support or results are compatibility changes.

#### Permitted matching deviations

An implementation may replace a reference behavior only with an alternative listed here. Each choice is independent, covers the shorthand and its complement in every position, including classes, and must be the same on every evaluation path. Without a declaration, the reference behavior applies.

| Declaration | Construct | Alternative behavior |
|-------------|-----------|----------------------|
| `digit: unicode` | `\d`, `\D` | Unicode decimal digits (`Nd`) and the complement. |
| `word: unicode` | `\w`, `\W` | Unicode word characters as in [UTS #18](https://www.unicode.org/reports/tr18/#Compatibility_Properties): `Alphabetic`, marks (`M`), `Nd`, connector punctuation (`Pc`), and `Join_Control`; and the complement. |
| `space: unicode` | `\s`, `\S` | Unicode `White_Space` and the complement. |

These are the default behaviors of Rust `regex`, so a Rust implementation can run expressions as written, with the same results as services that use that engine directly. The implementation declares the Unicode version it uses. An implementation may also adapt its engine internally to give the reference behavior.

For example, `^.$` on a single CR succeeds under the reference, whereas ECMA-262 fails it. `^\w+$` on `Привет` fails under the reference but succeeds with `word: unicode`. Such differences can change instance and trait validity.

The definitions are documented in [RE2 syntax](https://github.com/google/re2/wiki/Syntax), [Go syntax](https://pkg.go.dev/regexp/syntax), [Rust Unicode behavior](https://docs.rs/regex/latest/regex/#perl-character-classes-unicode-friendly), [ECMA-262 pattern semantics](https://tc39.es/ecma262/multipage/text-processing.html#sec-pattern-semantics), and [ECMA-262 whitespace](https://tc39.es/ecma262/multipage/ecmascript-language-lexical-grammar.html#sec-white-space).

### Execution safety

#### Why the subset alone is insufficient

The supported constructs allow expressions such as `(a*)*b`. On a long input consisting only of `a`, a conventional backtracking algorithm can explore exponentially many partitions before concluding that no `b` matches. This uses only literals, groups, and repetition. [V8's explanation](https://v8.dev/blog/non-backtracking-regexp#background-catastrophic-backtracking) illustrates the failure.

Restricting the language makes efficient matching possible; the execution strategy must actually provide the guarantee. **A safe engine is essential, not an optional extra safeguard.** The profile is not intended to prove arbitrary backtracking engines safe by analysing every permitted combination.

#### Required execution bound

A complete Boolean search must take **O(n + 1)** worst-case time for a fixed compiled expression, where n is input length. Every fallback must satisfy the same bound. A timeout alone does not establish it. An algorithm using backtracking is eligible only if it has that worst-case guarantee.

The constant may depend on the expression. [Rust `regex`](https://docs.rs/regex/latest/regex/#untrusted-haystacks) documents O(m × n) search time for `is_match`, where m includes expanded counted repetitions and n is input length in bytes. This is linear for fixed m; expression size and compilation costs still require bounds. The `+ 1` includes constant work on empty input.

The bound applies to the complete strategy used to answer whether a match exists. It does not automatically extend to enumerating all matches: Rust's [`find_iter` and `captures_iter`](https://docs.rs/regex/latest/regex/#iterating-over-matches) can take O(m × n²) over a full iteration.

#### Support bounds versus operational failures

- **Support bounds** are deterministic parts of the GTS profile, such as expression length and repetition limits. Exceeding them makes an expression unsupported. Membership must not depend on load, caches, or previous requests.
- **Operational failures** occur when memory exhaustion, an implementation's own limits such as compiled size, or an engine abort prevent evaluating a supported expression. They are errors, not evidence that an expression is outside the profile.

Linear search bounds each search, not the total cost of a validation: services that validate untrusted schemas or instances should limit input sizes and validation time at the deployment level.

### JSON Schema integration and errors

The same profile, declared semantics, and safe execution strategy must cover every regex path, including cached and generated validators. Replacing a single matching hook may leave format validation or property classification using another engine.

On explicit schema validation or registration with validation enabled, checks must cover all dialect-defined schema positions, including inactive branches, definitions, `x-gts-traits-schema`, and referenced schemas. Unsupported patterns must be detected before matching even when registration skipped validation. Literal data in `const`, `enum`, `default`, and `examples`, and unknown keywords, are not scanned as schemas unless a reference reaches them.

`format: "regex"` checks membership and support under the same policy as schema patterns; it does not execute the expression. Equivalent bounded checks, including parsers and caches, are allowed.

| Situation | Required result |
|-----------|-----------------|
| A completed search finds no match | Ordinary matching result. `pattern` fails; `patternProperties` does not apply that subschema to the unmatched property. Normal keyword and applicator semantics apply. |
| A schema pattern is outside the profile or its support bounds | Schema error before matching; not invertible by `not`. |
| A regex-valued string is outside the profile or its support bounds | Ordinary `format: "regex"` violation; invertible by `not`. |
| Parsing, compilation, or evaluation cannot complete because of operational exhaustion or an engine abort | Whole-validation error; never a non-match, format violation, skipped constraint, or failure inverted by `not`. |

### Remaining work and conformance

Before publishing the profile, check the intended runtimes, including browsers, for profile recognition, safe execution, and coverage of every JSON Schema regex path.

Conformance must cover accepted and rejected syntax, support boundaries, common matching results, each permitted deviation and its declaration, and consistent behavior across all evaluation paths. Rejecting an expression within the profile and its bounds as unsupported because the chosen engine lacks the feature is nonconforming.

ReDoS stress cases, including repeated successful matches, can detect regressions but do not prove complexity bounds. Operational failures may need local fault-injection checks because the black-box API cannot always trigger or distinguish them portably.

### Implementation references

- [Ajv `code.regExp`](https://ajv.js.org/options.html#code-v7): replacement matching engine; format and generated/cached paths still need assessment.
- [python-jsonschema extension API](https://python-jsonschema.readthedocs.io/en/stable/creating/), [keyword handlers](https://github.com/python-jsonschema/jsonschema/blob/main/jsonschema/_keywords.py), and [property-classification helpers](https://github.com/python-jsonschema/jsonschema/blob/main/jsonschema/_utils.py): several handlers using `re.search` may need coordinated replacement.
- [Rust `jsonschema` regex configuration](https://docs.rs/jsonschema/latest/jsonschema/#regular-expression-configuration): assess matching, format support, and error handling together.
- [RE2 guarantees](https://github.com/google/re2#readme), [RE2/J](https://github.com/google/re2j), and [RE2JS](https://github.com/le0pard/re2js): candidate engines; conformance must be established for the selected implementation and version.

Where library hooks are incomplete, a plugin, fork, or different library may be required. A built-in JavaScript `RegExp` or a successful profile parse alone does not establish the execution guarantee.
