"""Regular-expression validation tests (OP#6 and OP#13).

Covers README §11.0.1 (ADR-0006, Option 4) for `pattern`, `patternProperties`,
`propertyNames`, and `format: "regex"` in instance and trait validation,
including the property classification used by `additionalProperties` and
`unevaluatedProperties`.

GTS defines one closed syntax profile, a subset of both ECMA-262 `u` and RE2
syntax. Matching follows RE2 semantics as defined by GTS, except for deviations
that GTS permits and each implementation declares. The tests keep these
questions apart:

- Support: expressions outside both syntaxes, spellings that the engines read
  differently, and constructs the profile excludes must be rejected; the
  supported constructs of README §11.0.1 must be supported. Every evaluation path must agree, but agreement
  alone is not sufficient.
- Reference matching: completed searches must give the reference (RE2)
  results in every path, for cases that no permitted deviation affects.
- Matching differences: cases that a permitted deviation in ADR-0006 affects
  expect the reference result unless the test runner declares the
  implementation's alternative, which is then required instead.
- Safety and failures: explicit, non-invertible failures, checking of every
  schema position, and response bounds for known ReDoS regressions.

The API reports only `ok` and an error string, so a payload mismatch and an
operational failure look alike. Where the difference matters, a test also
validates against a negated schema and requires complementary results. This is
a consistency probe for stable conditions, not a classifier: the two results
come from independent requests, so a transient failure on either side can be
read as a verdict. Operational failures cannot be triggered portably;
implementations should test them locally, for example with fault injection.

Stress tests detect known regressions by bounding response time. They do not
prove a complexity bound, and a client timeout does not stop the server.

Environment variables:

- `GTS_TEST_REGEX_DECLARED_BEHAVIOR`: JSON object naming the permitted matching
  deviation the implementation declares for each construct, for example
  `{"digit": "unicode", "word": "unicode", "space": "unicode"}` for Rust
  `regex` defaults. Constructs left out use the reference behavior. See
  `_PERMITTED_BEHAVIORS`.
- `GTS_TEST_REGEX_STRESS_SECONDS`: response time limit for stress cases
  (default 2).
"""

import json
import os
import time

import pytest

from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    register as _register,
    register_derived as _register_derived,
    register_instance as _register_instance,
    validate_instance as _validate_instance,
    validate_type_schema as _validate_type_schema,
)
from httprunner import HttpRunner, Config

_STRESS_SECONDS = float(os.environ.get("GTS_TEST_REGEX_STRESS_SECONDS", "2"))
_DRAFT_07 = "http://json-schema.org/draft-07/schema#"
_DRAFT_2019_09 = "https://json-schema.org/draft/2019-09/schema"
_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


# ---------------------------------------------------------------------------
# Declared matching behavior
# ---------------------------------------------------------------------------

# Alternatives from ADR-0006 "Permitted matching deviations", the defaults of
# Rust `regex`.
_PERMITTED_BEHAVIORS = {
    # Unicode decimal digits (Nd).
    "digit": ("unicode",),
    # Unicode word characters (UTS #18).
    "word": ("unicode",),
    # Unicode White_Space.
    "space": ("unicode",),
}


def _parse_declared_behavior(text):
    """Parses `GTS_TEST_REGEX_DECLARED_BEHAVIOR`; constructs default to reference."""
    if not text.strip():
        return {}
    declared = json.loads(text)
    if not isinstance(declared, dict):
        raise ValueError("GTS_TEST_REGEX_DECLARED_BEHAVIOR must be a JSON object")
    for construct, behavior in declared.items():
        if construct not in _PERMITTED_BEHAVIORS:
            raise ValueError(f"unknown construct {construct!r}")
        allowed = ("reference",) + _PERMITTED_BEHAVIORS[construct]
        if behavior not in allowed:
            raise ValueError(f"{construct!r} behavior must be one of {allowed}")
    return declared


_DECLARED_BEHAVIOR = _parse_declared_behavior(
    os.environ.get("GTS_TEST_REGEX_DECLARED_BEHAVIOR", "")
)


# ---------------------------------------------------------------------------
# Expressions by support category
# ---------------------------------------------------------------------------

# The six-character regex source backslash, "u", "0041". Built by concatenation
# so that no tool can decode it to the permitted literal `A`.
_UNICODE_REGEX_ESCAPE = "\\" + "u0041"

# Syntax errors in both ECMA-262 `u` and RE2.
_MALFORMED_REGEX_STRINGS = (
    ("lone_bracket", "["),
    ("unterminated_class", "[unclosed"),
    ("unterminated_group", "(unclosed"),
    ("unmatched_paren", "a)"),
    ("reversed_quantifier", "a{3,2}"),
    ("trailing_backslash", "\\"),
    ("leading_quantifier", "*abc"),
    ("reversed_range", "[z-a]"),
)

# Rejected by ECMA-262 `u` or RE2 syntax, so outside any common subset.
_OUTSIDE_COMMON_SYNTAX = (
    # ECMA-262 `u` only.
    ("control_escape", r"\cA"),
    ("lookahead", "a(?=b)"),
    ("negative_lookahead", "a(?!b)"),
    ("lookbehind", "(?<=a)b"),
    ("negative_lookbehind", "(?<!a)b"),
    ("backreference", r"^(a+)\1$"),
    ("named_backreference", r"^(?<w>a)\k<w>$"),
    # A regex escape, not the JSON escape that decodes to `A` (ADR-0006).
    ("unicode_escape", _UNICODE_REGEX_ESCAPE),
    # RE2 only.
    ("identity_escape", r"\@"),
    ("octal_escape", r"\012"),
    ("quoted_literal", r"\Qx.y\E"),
    ("ungreedy_flag", "(?U)a+"),
    ("case_insensitive_flag", "(?i)abc"),
    ("absolute_end", r"abc\z"),
    ("braced_hex_escape", r"\x{41}"),
    ("posix_class", "[[:alpha:]]"),
    # RE2, but not Go.
    ("byte_match", r"\C"),
    # Neither.
    ("atomic_group", "(?>a+)b"),
    ("possessive", "a++b"),
    ("stacked_quantifier", "a**"),
)

# Accepted by both syntaxes but excluded from the initial profile: README
# §11.0.1 excludes inline modifiers, and ADR-0006 lists the others.
_EXCLUDED_BY_DRAFT = (
    ("scoped_inline_modifier", "(?i:a)b"),
    ("named_group", "(?<w>a)"),
    ("unicode_property", r"^\p{L}+$"),
    ("word_boundary", r"\ba\b"),
    ("non_word_boundary", r"a\B"),
    # ECMA-262 `u` reads it as NUL, RE2 as octal.
    ("nul_escape", r"\0"),
)

# Spellings that ECMA-262 `u`, RE2, and Rust `regex` read differently, or that
# only some of them accept (README §11.0.1 "Spelling rules").
_AMBIGUOUS_SPELLINGS = (
    # RE2 reads a count with a leading zero as literal text.
    ("leading_zero_count", "a{01}"),
    ("space_in_count", "a{1, 2}"),
    # RE2 reads a missing lower count as literal text.
    ("missing_lower_count", "a{,3}"),
    ("unescaped_close_bracket", "a]"),
    ("unescaped_close_brace", "a}"),
    ("unescaped_open_brace", "a{b"),
    ("escaped_hyphen_outside_class", r"\-"),
    ("stacked_counted_repetition", "a{2}{3}"),
    ("quantified_anchor", "^*"),
    ("empty_class", "[]"),
    ("empty_negated_class", "[^]"),
    ("unescaped_open_bracket_in_class", "[a[]"),
    ("leading_close_bracket_in_class", "[]a]"),
    ("hyphen_inside_class", "[a-c-e]"),
    ("shorthand_range_endpoint", r"[\d-z]"),
    # Rust `regex` reads doubled `&`, `-`, and `~` in a class as set
    # operations, also where they adjoin a range.
    ("class_intersection_spelling", "[a&&b]"),
    ("class_difference_spelling", "[a--b]"),
    ("class_symmetric_difference_spelling", "[a~~b]"),
    ("class_difference_after_range", "[!--0]"),
)

# The supported constructs (README §11.0.1 "Supported constructs").
_PROFILE_REGEX_STRINGS = (
    ("empty", ""),
    ("literal", "abc"),
    ("unicode_literal", "é😀"),
    ("anchored_class", "^[A-Za-z0-9]+$"),
    ("negated_class", "[^abc]"),
    ("group_alternation", "(foo|bar)+"),
    ("non_capturing_group", "(?:ab)+"),
    ("range_bounded", "[a-z]{1,3}"),
    ("exact_repeat", "a{3}"),
    ("open_repeat", "a{2,}"),
    ("nested_groups", "(a(b)?c)*"),
    ("lazy_quantifier", "a.*?b"),
    ("lazy_forms", "a*?b+?c??d{1,2}?e{2,}?f{2}?"),
    ("escaped_metachar", r"\(x\)\.\*"),
    ("escaped_syntax_chars", r"\/\^\$\+\?\{\}\|\[\]"),
    ("escaped_backslash", r"\\C"),
    ("character_escapes", r"\n\r\t\f\v"),
    ("hex_escape", r"\x41"),
    ("shorthand_classes", r"\d\D\w\W\s\S"),
    # Class spellings near the spelling rules: punctuation is literal in a
    # class, and escaped or hex-spelled characters are not operators.
    ("class_punctuation", "[a^$.*+?(){}|]"),
    ("class_escaped_leading_bracket", r"[\]a]"),
    ("class_escaped_hyphen_range", r"[\--0]"),
    ("class_hex_ampersand", r"[&\x26]"),
    ("class_hex_tilde", r"[~\x7e]"),
    ("class_leading_hyphen", "[-a]"),
    ("class_trailing_hyphen", "[a-]"),
    ("class_shorthand_hyphen", r"[\w-]"),
    ("class_escapes", r"[\[\n]"),
    ("class_hex_range", r"[\x41-\x5A]"),
    ("zero_repeat", "a{0}"),
    ("empty_alternative", "(?:|a)"),
    ("anchors_and_dot", "^a.c$"),
    # In-profile expressions that backtracking engines handle exponentially.
    ("nested_star", "(a*)*b"),
    ("nested_plus", "(a+)+$"),
    ("ambiguous_alternation", "^(a|aa)+$"),
    ("ambiguous_branches", r"^(?:(a|aa)+$|a+!$)"),
    # At the common support bounds (ADR-0006 "Common support bounds").
    ("repeat_1000", "a{1000}"),
    ("nested_repeat_product_1000", "(?:a{10}){100}"),
    ("open_repeat_1000", "a{1000,}"),
    # Four times (6 + 1000), plus 72: expanded length exactly 4096.
    ("expanded_length_4096", "a{1000}" * 4 + "a" * 72),
    ("literal_4096", "a" * 4096),
    # Large compiled programs: Unicode complements and classes at the bounds.
    ("complement_repeats_at_bounds", r"\S{1000}\W{1000}"),
    ("negated_class_repeat_at_bounds", r"[^\s\d]{580}"),
    # Code points, not UTF-8 bytes or UTF-16 code units.
    ("astral_4096", "😀" * 4096),
    # Upper counts multiply: 10 * 100.
    ("nested_upper_count_1000", "(?:a{1,10}){100}"),
    # `*` contributes one to the product.
    ("star_over_repeat_1000", "(?:a{1000})*"),
    ("group_nesting_32", "(" * 32 + "a" + ")" * 32),
    # Each level is a repetition, a group, an alternation and a concatenation.
    ("mixed_nesting_32", "(a|a" * 32 + "X" + ")*" * 32),
    # The same, with root alternation and a class of translated shorthands.
    ("mixed_nesting_32_classes", "z|x" + "(a|a" * 32 + r"[\s\S\w\W\d\D]*?" + ")*" * 32),
)

# Just beyond the common support bounds.
_OUTSIDE_BOUNDS = (
    ("repeat_above_1000", "a{1001}"),
    ("nested_repeat_2000", "(?:a{1000}){2}"),
    ("open_nested_repeat_2000", "(?:a{1000,}){2}"),
    ("expanded_length_4097", "a{1000}" * 4 + "a" * 73),
    ("literal_4097", "a" * 4097),
    ("astral_4097", "😀" * 4097),
    # Expanded length 2025, product 10 * 101.
    ("nested_upper_count_1010", "(?:a{1,10}){101}"),
    # A zero count contributes one, so the product is 1000 * 2.
    ("zero_count_product_2000", "((a{1000}){0}){2}"),
    # 1000 copies of the six-character group: expanded length 6006.
    ("repeated_group_expansion", "(?:ab){1000}"),
    ("group_nesting_33", "(" * 33 + "a" + ")" * 33),
)

_EXPECTED_SUPPORT = {
    "malformed": False,
    "outside_common_syntax": False,
    "ambiguous_spelling": False,
    "excluded_by_draft": False,
    "outside_bounds": False,
    "profile": True,
}

_SUPPORT_CASES = tuple(
    (category, label, expr)
    for category, cases in (
        ("malformed", _MALFORMED_REGEX_STRINGS),
        ("outside_common_syntax", _OUTSIDE_COMMON_SYNTAX),
        ("ambiguous_spelling", _AMBIGUOUS_SPELLINGS),
        ("excluded_by_draft", _EXCLUDED_BY_DRAFT),
        ("outside_bounds", _OUTSIDE_BOUNDS),
        ("profile", _PROFILE_REGEX_STRINGS),
    )
    for label, expr in cases
)

_REJECTED_REGEX_STRINGS = (
    _MALFORMED_REGEX_STRINGS
    + _OUTSIDE_COMMON_SYNTAX
    + _AMBIGUOUS_SPELLINGS
    + _EXCLUDED_BY_DRAFT
    + _OUTSIDE_BOUNDS
)

# Expressions outside the profile used for schema-position checks: one
# malformed, and one each that ECMA-262 `u` alone, RE2 alone, and ECMA-262 `u`
# and Rust but not RE2 accept, plus one that both accept but the draft excludes.
_PREFLIGHT_EXPRESSIONS = (
    ("malformed", "["),
    ("ecma_only", "a(?=b)"),
    ("re2_only", r"abc\z"),
    ("not_re2", _UNICODE_REGEX_ESCAPE),
    ("draft_excluded", "(?i:a)b"),
    # Accepted by both engines, but beyond the support bounds.
    ("out_of_bounds", "a{1000}" * 4 + "a" * 73),
)


# ---------------------------------------------------------------------------
# Matching cases
# ---------------------------------------------------------------------------

# Reference (RE2) results that no permitted deviation changes. Shorthand
# classes are probed with ASCII only. `.` matches CR, U+2028, and U+2029,
# unlike ECMA-262. Paired astral code points follow the code-point model;
# unpaired surrogates are not valid GTS input and are not used.
_MATCH_CASES = (
    ("unanchored_search", "abc", ("abc", "xabcx"), ("ab", "a-b-c")),
    ("case_sensitive", "^abc$", ("abc",), ("ABC", "Abc", "xabc", "abcx")),
    (
        "multiline_off",
        "^abc$",
        ("abc",),
        # `$` without `m` does not match before a final newline.
        ("x\nabc\ny", "abc\nx", "x\nabc", "abc\n"),
    ),
    ("dot_all_off", "^a.c$", ("abc", "a-c", "a c"), ("a\nc", "ac", "abbc")),
    ("empty", "", ("", "abc"), ()),
    ("class", "^[a-z]+$", ("abc", "z"), ("", "abc1", "ABC")),
    ("negated_class", "^[^0-9]+$", ("abc", "a-b"), ("a1", "")),
    ("alternation", "^(foo|bar)+$", ("foo", "foobar", "barfoo"), ("fooba", "", "baz")),
    ("non_capturing_group", "^(?:ab)+$", ("ab", "abab"), ("aba", "")),
    ("counted_repetition", "^a{2,3}$", ("aa", "aaa"), ("a", "aaaa")),
    ("open_repetition", "^a{2,}$", ("aa", "aaaa"), ("a", "")),
    (
        "exact_repetition",
        "[0-9]{3}-[0-9]{4}",
        ("555-1234", "x555-1234y"),
        ("55-1234", "555-123"),
    ),
    ("optional_and_star", "^ab?c*$", ("a", "ab", "acc", "abcc"), ("b", "abb")),
    ("lazy_quantifier", "^a.*?b$", ("ab", "axxb"), ("a", "ba")),
    ("lazy_forms", "^a+?b??c{1,2}?$", ("ac", "abcc", "aabc"), ("a", "bc", "accc")),
    ("escaped_metacharacters", r"^\(a\.b\)\*$", ("(a.b)*",), ("(axb)*", "a.b")),
    ("character_escapes", r"^\t\n\r\f\v$", ("\t\n\r\f\v",), ("\t\n\r\f", " \n\r\f\v")),
    ("hex_escape", r"^\x41$", ("A",), ("a", "x41")),
    # A code point, not a UTF-8 byte.
    ("hex_escape_latin1", r"^\xE9$", ("é",), ("e", "xE9", "Ã©")),
    ("zero_repetition", "^a{0}$", ("",), ("a",)),
    ("empty_alternative", "^(?:|a)$", ("", "a"), ("aa", "b")),
    ("nested_quantifiers", "(a+)+$", ("a", "aaaa"), ("", "aaab")),
    ("digit_ascii", r"^\d+$", ("0123456789",), ("", "a", " ", "-", "1a")),
    ("non_digit_ascii", r"^\D$", ("a", " ", "-"), ("0", "9")),
    ("word_ascii", r"^\w+$", ("azAZ09_",), ("", "-", " ", "a-b")),
    ("non_word_ascii", r"^\W$", ("-", " ", "!"), ("a", "Z", "0", "_")),
    ("space_ascii", r"^\s+$", (" ", "\t\n\f\r"), ("", "a", "_")),
    ("non_space_ascii", r"^\S$", ("a", "-"), (" ", "\t", "\n")),
    # Shorthands inside classes, including negated classes.
    ("class_digit_ascii", r"^[\d]+$", ("0123456789",), ("", "a", "1a")),
    ("class_word_hyphen", r"^[\w-]+$", ("a-b_0",), ("", "a b", "a.b")),
    ("class_negated_space", r"^[^\s]$", ("a", "-"), (" ", "\t", "\n")),
    ("dot_ascii", "^.$", ("a", " ", "\t"), ("", "\n", "ab")),
    ("dot_line_terminators", "^.$", ("\r", "\u2028", "\u2029"), ("\n",)),
    ("code_point_dot", "^.$", ("😀", "é"), ("😀😀",)),
    ("code_point_count", "^.{2}$", ("ab", "😀a"), ("😀",)),
    ("code_point_negated_class", "^[^a]$", ("😀",), ("a", "😀😀")),
    ("astral_literal", "^😀+$", ("😀", "😀😀"), ("", "😀a")),
    ("astral_class_literal", "^[😀é]$", ("😀", "é"), ("😀é",)),
    ("astral_range", "^[😀-😂]$", ("😀", "😁", "😂"), ("😃", "a", "😀😀")),
)

# Probes that a permitted deviation in ADR-0006 changes: construct, label,
# pattern, probe, reference result, and the result under each alternative.
_DIFFERENCE_CASES = (
    ("digit", "digit_arabic_indic", r"^\d$", "\u0661", False, {"unicode": True}),
    ("digit", "non_digit_arabic_indic", r"^\D$", "\u0661", True, {"unicode": False}),
    ("word", "word_e_acute", r"^\w$", "é", False, {"unicode": True}),
    ("word", "non_word_e_acute", r"^\W$", "é", True, {"unicode": False}),
    ("space", "space_vertical_tab", r"^\s$", "\v", False, {"unicode": True}),
    ("space", "space_nbsp", r"^\s$", "\u00a0", False, {"unicode": True}),
    ("space", "space_bom", r"^\s$", "\ufeff", False, {"unicode": False}),
    ("space", "space_next_line", r"^\s$", "\u0085", False, {"unicode": True}),
    ("space", "non_space_nbsp", r"^\S$", "\u00a0", True, {"unicode": False}),
    # The declaration also applies inside classes, including negated classes.
    ("digit", "class_non_digit_arabic_indic", r"^[^\d]$", "\u0661", True, {"unicode": False}),
    ("word", "class_word_e_acute", r"^[\w]$", "é", False, {"unicode": True}),
    ("space", "class_space_nbsp", r"^[\s]$", "\u00a0", False, {"unicode": True}),
    ("space", "class_non_space_vertical_tab", r"^[^\s]$", "\v", True, {"unicode": False}),
    # The UTS #18 word set, independent of the digit declaration.
    ("word", "word_arabic_indic_digit", r"^\w$", "\u0661", False, {"unicode": True}),
    ("word", "word_combining_mark", r"^\w$", "\u0301", False, {"unicode": True}),
    ("word", "word_zero_width_joiner", r"^\w$", "\u200d", False, {"unicode": True}),
)


# ---------------------------------------------------------------------------
# Expectation checks
# ---------------------------------------------------------------------------


def _check_support(expression, expected, support):
    """Requires every path to agree on `expression` and on `expected`.

    `support` maps each evaluation path to whether it accepted the expression.
    """
    values = set(support.values())
    assert len(values) == 1, ("paths disagree on support", expression, support)
    (supported,) = values
    assert supported is expected, (
        "must be supported" if expected else "must be rejected",
        expression,
        support,
    )


def _check_matches(pattern, probe, verdicts, expected):
    """Requires every path to agree on `probe` and, if given, `expected`."""
    values = set(verdicts.values())
    assert len(values) == 1, ("paths disagree on match", pattern, probe, verdicts)
    (matched,) = values
    if expected is not None:
        assert matched is expected, (
            "must match" if expected else "must not match",
            pattern,
            probe,
            verdicts,
        )
    return matched


def _declared_expectation(construct, reference, alternatives, declared):
    """Expected result under the declared behavior for `construct`."""
    behavior = declared.get(construct, "reference")
    if behavior == "reference":
        return reference
    return alternatives[behavior]


# ---------------------------------------------------------------------------
# OP#6 - instance validation
# ---------------------------------------------------------------------------

_REGEX_FORMAT_TYPE_ID = "gts.x.test6.formats.regexsafe.v1~"
_REGEX_FORMAT_SCHEMA = {
    "type": "object",
    "required": ["regexValue"],
    "properties": {"regexValue": {"type": "string", "format": "regex"}},
}


class TestCaseTestOp6Validation_RegexFormat(HttpRunner):
    """OP#6 asserts `format: regex` on instance values (README §11.0.1)."""

    config = Config("OP#6 Extended - Regex format Conformance").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        _register(
            f"gts://{_REGEX_FORMAT_TYPE_ID}",
            _REGEX_FORMAT_SCHEMA,
            "register schema with regex format",
        ),
        *[
            _register_instance(
                {
                    "type": _REGEX_FORMAT_TYPE_ID,
                    "id": f"{_REGEX_FORMAT_TYPE_ID}x.test6._.regex_valid_{label}.v1.0",
                    "regexValue": pattern,
                },
                f"register instance with profile regex ({label})",
            )
            for label, pattern in _PROFILE_REGEX_STRINGS
        ],
        *[
            _validate_instance(
                f"{_REGEX_FORMAT_TYPE_ID}x.test6._.regex_valid_{label}.v1.0",
                True,
                f"accept profile regex ({label})",
            )
            for label, _ in _PROFILE_REGEX_STRINGS
        ],
        *[
            _register_instance(
                {
                    "type": _REGEX_FORMAT_TYPE_ID,
                    "id": f"{_REGEX_FORMAT_TYPE_ID}x.test6._.regex_invalid_{label}.v1.0",
                    "regexValue": pattern,
                },
                f"register instance with out-of-profile regex ({label})",
            )
            for label, pattern in _REJECTED_REGEX_STRINGS
        ],
        *[
            _validate_instance(
                f"{_REGEX_FORMAT_TYPE_ID}x.test6._.regex_invalid_{label}.v1.0",
                False,
                f"reject out-of-profile regex ({label})",
            )
            for label, _ in _REJECTED_REGEX_STRINGS
        ],
    ]


# The explicit class that ADR-0006 suggests for ECMA-262 `.` results: JSON
# escapes put literal U+2028 and U+2029 into the expression; no regex escape
# syntax is needed for them.
_ECMA_DOT_PATTERN = "^P[^\\n\\r\u2028\u2029]+"
_DURATION_PATTERN = (
    "^P(?:[0-9]+Y)?(?:[0-9]+M)?(?:[0-9]+D)?"
    "(?:T(?:[0-9]+H(?:[0-9]+M)?(?:[0-9]+S)?|[0-9]+M(?:[0-9]+S)?|[0-9]+S))?$"
)

_ECMA_DOT_MATCHES = (
    "P90D",
    "PT1H",
    "P1Y2M3DT4H5M6S",
    "P0D",
    "PX",
    "P ",
    "P😀",
    "P1\n",
)
_ECMA_DOT_NON_MATCHES = (
    "P",
    "",
    "90D",
    "p90d",
    "XP1D",
    " P1D",
    "P\n",
    "P\r",
    "P\u2028",
    "P\u2029",
    "\nP1D",
)
_DURATION_MATCHES = (
    "P1Y",
    "P1M",
    "P1D",
    "P1Y2M3D",
    "P1Y3D",
    "P2M10D",
    "PT1H",
    "PT1M",
    "PT1S",
    "PT1H30M",
    "P1DT12H",
    "P1Y2M3DT4H5M6S",
    "P10Y",
)
_DURATION_NON_MATCHES = (
    "P",
    "PT",
    "P1DT",
    "",
    "P1W",
    "P1H",
    "PT1D",
    "P1Y1Y",
    "P1D1Y",
    "P1M1Y",
    "P1.5D",
    "P-1D",
    "1Y",
    "p1d",
    "P1Y ",
    " P1Y",
    "P1YT1D",
    "PT1H1D",
)

_ATTACK_CASES = (
    (r"^(a+)+$", "a" * 50_000 + "!"),
    (r"^(a|aa)+$", "a" * 50_000 + "!"),
    (r"^a*a*a*b$", "a" * 50_000 + "!"),
    (_DURATION_PATTERN, "P" + "1" * 50_000 + "!"),
)

# Ambiguous expressions that backtracking engines handle exponentially. The
# second alternative matches the stress keys, so a complete search succeeds.
_PATTERN_PROPERTIES_STRESS_PATTERN = r"^(?:(a+)+$|a+!$)"
_AMBIGUOUS_PATTERN = r"^(?:(a|aa)+$|a+!$)"
# Optional copies before mandatory ones: backtracking tries the optional copies
# exponentially often. Expanded length 3512 and product 500, within the bounds.
_COUNTED_REPETITION_PATTERN = "^(?:a?){500}a{500}$"


def _post_schema(gts_session, gts_base_url, type_id, body, dialect, validate):
    params = {"validate": "true" if validate else "false"}
    return gts_session.post(
        f"{gts_base_url}/entities",
        params=params,
        json={"$id": f"gts://{type_id}", "$schema": dialect, "type": "object", **body},
        timeout=30,
    )


def _regexp_type_id(name):
    return f"gts.x.test6regexp._.{name}.v1~"


def _register_regexp_type(gts_session, gts_base_url, name, body, dialect=_DRAFT_07):
    """Registers a schema with validation and requires it to be accepted."""
    type_id = _regexp_type_id(name)
    response = _post_schema(gts_session, gts_base_url, type_id, body, dialect, True)
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True, response.json()
    return type_id


def _try_register(gts_session, gts_base_url, type_id, body, dialect=_DRAFT_07):
    """Registers a schema with validation; returns None if it is rejected."""
    response = _post_schema(gts_session, gts_base_url, type_id, body, dialect, True)
    assert response.status_code in (200, 422), response.text
    if response.status_code == 422:
        _assert_explicit_validation_error(response.json(), (type_id, body))
        return None
    assert response.json()["ok"] is True, response.json()
    return type_id


def _assert_schema_rejected(gts_session, gts_base_url, name, body, dialect=_DRAFT_07):
    type_id = _regexp_type_id(name)
    response = _post_schema(gts_session, gts_base_url, type_id, body, dialect, True)
    assert response.status_code == 422, response.text
    _assert_explicit_validation_error(response.json(), (name, body))


def _validate_type_schema_json(gts_session, gts_base_url, type_id):
    response = gts_session.post(
        f"{gts_base_url}/validate-type-schema",
        json={"type_id": type_id},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _assert_deferred_schema_rejected(
    gts_session, gts_base_url, name, body, dialect=_DRAFT_07
):
    """Registers without validation; explicit schema validation must fail.

    Returns the type ID, or None if the implementation checked the expression
    eagerly and rejected the registration.
    """
    type_id = _regexp_type_id(name)
    response = _post_schema(gts_session, gts_base_url, type_id, body, dialect, False)
    # Implementations may check expressions eagerly at registration.
    if response.status_code == 422:
        _assert_explicit_validation_error(response.json(), (name, "registration"))
        return None
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True, response.json()
    _assert_explicit_validation_error(
        _validate_type_schema_json(gts_session, gts_base_url, type_id),
        (name, "explicit schema validation"),
    )
    return type_id


def _validate_json(gts_session, gts_base_url, type_id, instance, timeout=30):
    response = gts_session.post(
        f"{gts_base_url}/validate-json/{type_id}",
        json=instance,
        timeout=timeout,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _validate_json_under_stress(gts_session, gts_base_url, type_id, instance):
    started = time.perf_counter()
    result = _validate_json(
        gts_session, gts_base_url, type_id, instance, timeout=_STRESS_SECONDS
    )
    elapsed = time.perf_counter() - started
    assert elapsed < _STRESS_SECONDS, (type_id, elapsed)
    return result


def _assert_explicit_validation_error(result, context):
    assert result["ok"] is False, (context, result)
    error = result.get("error")
    assert isinstance(error, str) and error.strip(), (context, result)


def _value_body(value_schema):
    return {"required": ["value"], "properties": {"value": value_schema}}


def _pattern_body(pattern, min_length=0):
    return _value_body({"type": "string", "pattern": pattern, "minLength": min_length})


def _negated_body(body):
    return {"not": body}


def _classification_body(pattern, keyword="additionalProperties"):
    return {
        "patternProperties": {pattern: {"type": "integer"}},
        keyword: False,
    }


def _trait_schema_body(value_schema):
    return {
        "x-gts-traits-schema": {
            "type": "object",
            "properties": {"value": value_schema},
        }
    }


def _register_verdict_pair(gts_session, gts_base_url, name, body, dialect=_DRAFT_07):
    """Registers `body` and `not: body` for complementary verdicts."""
    return (
        _register_regexp_type(gts_session, gts_base_url, name, body, dialect),
        _register_regexp_type(
            gts_session, gts_base_url, f"{name}_negated", _negated_body(body), dialect
        ),
    )


def _complementary(positive, negated, context):
    """The verdict of `positive`, required to be the complement of `negated`.

    A genuine verdict is inverted by `not`, while a persistent operational
    failure fails both. Under stable conditions this detects such a failure;
    a transient failure on one side cannot be told apart from a verdict.
    """
    assert positive["ok"] is not negated["ok"], (context, positive, negated)
    _assert_explicit_validation_error(negated if positive["ok"] else positive, context)
    return positive["ok"]


def _verdict(gts_session, gts_base_url, pair, instance):
    """Whether `instance` validates against the first type of `pair`."""
    positive = _validate_json(gts_session, gts_base_url, pair[0], instance)
    negated = _validate_json(gts_session, gts_base_url, pair[1], instance)
    return _complementary(positive, negated, instance)


def _assert_pattern_matches(gts_session, gts_base_url, pair, matches, non_matches):
    for value in matches:
        assert _verdict(gts_session, gts_base_url, pair, {"value": value}), value
    for value in non_matches:
        assert not _verdict(gts_session, gts_base_url, pair, {"value": value}), value


def _trait_verdict(gts_session, gts_base_url, bases, name, traits):
    """Whether `traits` satisfy the trait schema of the first of `bases`.

    A derived type of each base is registered without validation and then
    validated explicitly; the bases' trait schemas are complementary.
    """
    results = []
    for base_id in bases:
        derived_id = f"{base_id}x.test13._.{name}.v1~"
        response = _post_schema(
            gts_session,
            gts_base_url,
            derived_id,
            {"allOf": [{"$ref": f"gts://{base_id}"}], "x-gts-traits": traits},
            _DRAFT_07,
            validate=False,
        )
        assert response.status_code == 200, response.text
        assert response.json()["ok"] is True, response.json()
        results.append(_validate_type_schema_json(gts_session, gts_base_url, derived_id))
    return _complementary(*results, (name, traits))


@pytest.fixture(scope="module")
def regex_format_types(gts_session, gts_base_url):
    """Types asserting `format: regex` on `value`, directly and under `not`."""
    return _register_verdict_pair(
        gts_session,
        gts_base_url,
        "regex_format_value",
        _value_body({"type": "string", "format": "regex"}),
    )


@pytest.fixture(scope="module")
def regex_trait_format_bases(gts_session, gts_base_url):
    """Trait schemas asserting `format: regex` on `value`, directly and under `not`."""
    return tuple(
        _register_regexp_type(
            gts_session, gts_base_url, name, _trait_schema_body(value_schema)
        )
        for name, value_schema in (
            ("regex_trait_format", {"type": "string", "format": "regex"}),
            (
                "regex_trait_format_negated",
                {"type": "string", "not": {"format": "regex"}},
            ),
        )
    )


# ---------------------------------------------------------------------------
# Evaluation paths
# ---------------------------------------------------------------------------

# Schema paths that evaluate an expression, each registered directly and
# under `not`.
_SCHEMA_PATHS = (
    "pattern",
    "ref_definition",
    "inherited",
    "property_names",
    "pattern_properties",
    "additional_properties",
    "unevaluated_properties",
    "trait",
)

# Paths for which a match verdict is obtained. The stored paths validate
# registered instances of the `pattern` types; `pattern_repeated` repeats the
# first request after the other paths have used the expression.
_VERDICT_PATHS = _SCHEMA_PATHS + ("stored_instance", "stored_entity", "pattern_repeated")

_VALUE_PATHS = ("pattern", "ref_definition", "inherited")


def _path_bodies(pattern):
    """Positive and negated bodies, with dialect, for each direct schema path."""
    value = {"type": "string", "pattern": pattern}
    bodies = {
        "pattern": (_value_body(value), _DRAFT_07),
        "property_names": ({"propertyNames": {"pattern": pattern}}, _DRAFT_07),
        "pattern_properties": (
            {"patternProperties": {pattern: {"type": "integer"}}},
            _DRAFT_07,
        ),
        "additional_properties": (
            _classification_body(pattern, "additionalProperties"),
            _DRAFT_07,
        ),
        "unevaluated_properties": (
            _classification_body(pattern, "unevaluatedProperties"),
            _DRAFT_2020_12,
        ),
    }
    paths = {
        path: ((body, _negated_body(body)), dialect)
        for path, (body, dialect) in bodies.items()
    }
    # The definition stays at the root so that the reference resolves under `not`.
    referenced = _value_body({"$ref": "#/definitions/value"})
    paths["ref_definition"] = (
        (
            {"definitions": {"value": value}, **referenced},
            {"definitions": {"value": value}, "not": referenced},
        ),
        _DRAFT_07,
    )
    paths["trait"] = (
        (
            _trait_schema_body(value),
            _trait_schema_body({"type": "string", "not": {"pattern": pattern}}),
        ),
        _DRAFT_07,
    )
    return paths


def _register_paths(gts_session, gts_base_url, name, pattern):
    """Registers every schema path of `pattern` with validation.

    Returns a (positive, negated) pair of type IDs per path, with None for a
    rejected registration. `inherited` derives from the `pattern` types.
    """
    paths = {}
    for path, ((body, negated), dialect) in _path_bodies(pattern).items():
        paths[path] = tuple(
            _try_register(
                gts_session, gts_base_url, _regexp_type_id(type_name), schema, dialect
            )
            for type_name, schema in (
                (f"{name}_{path}", body),
                (f"{name}_{path}_negated", negated),
            )
        )
    paths["inherited"] = tuple(
        None
        if base_id is None
        else _try_register(
            gts_session,
            gts_base_url,
            f"{base_id}x.test6regexp._.inherited.v1~",
            {"allOf": [{"$ref": f"gts://{base_id}"}]},
        )
        for base_id in paths["pattern"]
    )
    return paths


def _support_by_path(paths):
    support = {}
    for path, (positive, negated) in paths.items():
        support[path] = positive is not None
        support[f"{path}_negated"] = negated is not None
    return support


def _format_support(
    gts_session, gts_base_url, format_types, trait_bases, name, expression
):
    """`format: regex` verdicts on `expression` in an instance and in traits."""
    return {
        "format": _verdict(
            gts_session, gts_base_url, format_types, {"value": expression}
        ),
        "trait_format": _trait_verdict(
            gts_session, gts_base_url, trait_bases, name, {"value": expression}
        ),
    }


def _path_instance(path, probe):
    if path in _VALUE_PATHS:
        return {"value": probe}
    if path == "pattern_properties":
        # A matching name applies the failing value constraint.
        return {probe: "not-an-integer"}
    # A non-matching name is rejected by propertyNames or the closed object.
    return {probe: 1}


def _stored_instance_verdicts(gts_session, gts_base_url, pair, name, probe):
    """Verdicts for stored instances through both instance-validation endpoints."""
    results = {"stored_instance": [], "stored_entity": []}
    for type_id in pair:
        instance_id = f"{type_id}x.test6regexp._.{name}.v1"
        response = gts_session.post(
            f"{gts_base_url}/entities",
            json={"id": instance_id, "type": type_id, "value": probe},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        assert response.json()["ok"] is True, response.json()
        for path, endpoint, key in (
            ("stored_instance", "validate-instance", "instance_id"),
            ("stored_entity", "validate-entity", "entity_id"),
        ):
            checked = gts_session.post(
                f"{gts_base_url}/{endpoint}", json={key: instance_id}, timeout=30
            )
            assert checked.status_code == 200, checked.text
            results[path].append(checked.json())
    return {
        path: _complementary(*verdicts, (path, probe))
        for path, verdicts in results.items()
    }


def _path_verdicts(gts_session, gts_base_url, paths, name, probe):
    """Whether `probe` matches in each of `_VERDICT_PATHS`."""
    verdicts = {}
    for path in _SCHEMA_PATHS:
        pair = paths[path]
        if path == "trait":
            verdicts[path] = _trait_verdict(
                gts_session, gts_base_url, pair, name, {"value": probe}
            )
            continue
        valid = _verdict(gts_session, gts_base_url, pair, _path_instance(path, probe))
        verdicts[path] = not valid if path == "pattern_properties" else valid
    verdicts.update(
        _stored_instance_verdicts(gts_session, gts_base_url, paths["pattern"], name, probe)
    )
    verdicts["pattern_repeated"] = _verdict(
        gts_session, gts_base_url, paths["pattern"], {"value": probe}
    )
    return verdicts


@pytest.mark.parametrize(
    "category, label, expression",
    _SUPPORT_CASES,
    ids=[f"{case[0]}-{case[1]}" for case in _SUPPORT_CASES],
)
def test_regex_support(
    gts_session,
    gts_base_url,
    regex_format_types,
    regex_trait_format_bases,
    category,
    label,
    expression,
):
    """Support follows the profile category and is the same in every path.

    `format: regex` is checked before and after the schema registrations, so
    the result must not depend on caches or previous requests. A supported
    expression must also complete a search in every path: registration alone
    need not reach the engine.
    """
    name = f"support_{label}"
    support = {
        f"{path}_first": supported
        for path, supported in _format_support(
            gts_session,
            gts_base_url,
            regex_format_types,
            regex_trait_format_bases,
            f"{name}_first",
            expression,
        ).items()
    }
    paths = _register_paths(gts_session, gts_base_url, name, expression)
    support.update(_support_by_path(paths))
    support.update(
        {
            f"{path}_again": supported
            for path, supported in _format_support(
                gts_session,
                gts_base_url,
                regex_format_types,
                regex_trait_format_bases,
                f"{name}_again",
                expression,
            ).items()
        }
    )
    _check_support(expression, _EXPECTED_SUPPORT[category], support)
    if _EXPECTED_SUPPORT[category]:
        verdicts = _path_verdicts(gts_session, gts_base_url, paths, f"{name}_probe", "a")
        _check_matches(expression, "a", verdicts, None)


@pytest.mark.parametrize(
    "label, pattern, matches, non_matches",
    _MATCH_CASES,
    ids=[case[0] for case in _MATCH_CASES],
)
def test_reference_matching(
    gts_session,
    gts_base_url,
    regex_format_types,
    regex_trait_format_bases,
    label,
    pattern,
    matches,
    non_matches,
):
    """Completed searches give the reference result in every path."""
    name = f"match_{label}"
    support = _format_support(
        gts_session,
        gts_base_url,
        regex_format_types,
        regex_trait_format_bases,
        name,
        pattern,
    )
    paths = _register_paths(gts_session, gts_base_url, name, pattern)
    support.update(_support_by_path(paths))
    _check_support(pattern, True, support)
    cases = [(probe, True) for probe in matches] + [
        (probe, False) for probe in non_matches
    ]
    for index, (probe, expected) in enumerate(cases):
        verdicts = _path_verdicts(
            gts_session, gts_base_url, paths, f"{name}_p{index}", probe
        )
        _check_matches(pattern, probe, verdicts, expected)


@pytest.mark.parametrize(
    "construct, label, pattern, probe, reference, alternatives",
    _DIFFERENCE_CASES,
    ids=[case[1] for case in _DIFFERENCE_CASES],
)
def test_matching_differences_follow_declaration(
    gts_session, gts_base_url, construct, label, pattern, probe, reference, alternatives
):
    """Results that a permitted deviation changes follow the declared behavior.

    Without a declaration the reference result is required; with one, the
    declared alternative's result is required.
    """
    name = f"difference_{label}"
    paths = _register_paths(gts_session, gts_base_url, name, pattern)
    _check_support(pattern, True, _support_by_path(paths))
    verdicts = _path_verdicts(gts_session, gts_base_url, paths, f"{name}_p0", probe)
    expected = _declared_expectation(
        construct, reference, alternatives, _DECLARED_BEHAVIOR
    )
    _check_matches(pattern, probe, verdicts, expected)


def test_ecma_dot_class_matches(gts_session, gts_base_url):
    pair = _register_verdict_pair(
        gts_session, gts_base_url, "ecma_dot", _pattern_body(_ECMA_DOT_PATTERN)
    )
    _assert_pattern_matches(
        gts_session, gts_base_url, pair, _ECMA_DOT_MATCHES, _ECMA_DOT_NON_MATCHES
    )


def test_iso_duration_constraints_match(gts_session, gts_base_url):
    pair = _register_verdict_pair(
        gts_session,
        gts_base_url,
        "duration",
        _pattern_body(_DURATION_PATTERN, min_length=2),
    )
    _assert_pattern_matches(
        gts_session, gts_base_url, pair, _DURATION_MATCHES, _DURATION_NON_MATCHES
    )


def test_pattern_properties_matches(gts_session, gts_base_url):
    body = {
        "patternProperties": {
            r"[0-9]{3}px$": {"type": "integer"},
            r"^aa$": {"type": "string"},
        },
    }
    pair = _register_verdict_pair(gts_session, gts_base_url, "pattern_properties", body)
    assert _verdict(gts_session, gts_base_url, pair, {"123px": 1, "aa": "value"})
    for invalid_value in ({"123px": "not-an-integer"}, {"aa": 1}):
        assert not _verdict(gts_session, gts_base_url, pair, invalid_value)


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------
#
# The positive stress cases expect the server under test to complete the
# workload within GTS_TEST_REGEX_STRESS_SECONDS; tests/README.md describes the
# workload. It is a test-environment requirement, not a GTS minimum capacity.


def test_adversarial_inputs_fail_within_limit(gts_session, gts_base_url):
    for index, (pattern, attack_input) in enumerate(_ATTACK_CASES):
        type_id = _register_regexp_type(
            gts_session, gts_base_url, f"attack_{index}", _pattern_body(pattern)
        )
        result = _validate_json_under_stress(
            gts_session, gts_base_url, type_id, {"value": attack_input}
        )
        _assert_explicit_validation_error(result, pattern)


@pytest.mark.parametrize(
    "value, expected",
    [("a" * 500, True), ("a" * 500 + "!", False)],
    ids=["match", "non-match"],
)
def test_counted_repetition_completes_under_stress(
    gts_session, gts_base_url, value, expected
):
    """A counted repetition at the bounds completes within the response limit."""
    type_id = _register_regexp_type(
        gts_session,
        gts_base_url,
        "counted_repetition_stress",
        _pattern_body(_COUNTED_REPETITION_PATTERN),
    )
    result = _validate_json_under_stress(
        gts_session, gts_base_url, type_id, {"value": value}
    )
    if expected:
        assert result["ok"] is True, result
    else:
        _assert_explicit_validation_error(result, _COUNTED_REPETITION_PATTERN)


@pytest.mark.parametrize(
    "key",
    ["aaaa!", "a" * 64 + "!"],
    ids=["short-control", "backtracking-stress"],
)
def test_pattern_properties_rejects_invalid_value_under_stress(
    gts_session, gts_base_url, key
):
    """A matching property must never skip its value constraint under stress."""
    type_id = _register_regexp_type(
        gts_session,
        gts_base_url,
        "pattern_properties_resource_limits",
        {
            "patternProperties": {
                _PATTERN_PROPERTIES_STRESS_PATTERN: {"type": "integer"}
            }
        },
    )
    valid = _validate_json_under_stress(gts_session, gts_base_url, type_id, {key: 1})
    assert valid["ok"] is True, valid

    invalid = _validate_json_under_stress(
        gts_session, gts_base_url, type_id, {key: "not-an-integer"}
    )
    _assert_explicit_validation_error(
        invalid,
        "patternProperties must reject the wrong value type or report a regex "
        "resource error; the matching property must not be silently skipped",
    )


@pytest.mark.parametrize("keyword", ["pattern", "patternProperties"])
@pytest.mark.parametrize(
    "length", [4, 64], ids=["short-control", "backtracking-stress"]
)
def test_not_rejects_matching_instance_under_stress(
    gts_session, gts_base_url, keyword, length
):
    """Stress does not change the boolean result that `not` inverts."""
    matched = "a" * length + "!"
    if keyword == "pattern":
        body = _value_body({"type": "string", "not": {"pattern": _AMBIGUOUS_PATTERN}})
        valid_instance = {"value": "b"}
        invalid_instance = {"value": matched}
    else:
        # additionalProperties makes the inner schema fail if the matching key
        # is skipped, so treating a regex error as "no match" is observable too.
        body = {
            "not": {
                "patternProperties": {_AMBIGUOUS_PATTERN: {"type": "integer"}},
                "additionalProperties": False,
            }
        }
        valid_instance = {"aaaa!": "not-an-integer"}
        invalid_instance = {matched: 1}
    type_id = _register_regexp_type(
        gts_session, gts_base_url, f"not_{keyword.lower()}_resource_limits", body
    )

    valid = _validate_json(gts_session, gts_base_url, type_id, valid_instance)
    assert valid["ok"] is True, valid

    # These instances satisfy the schema inside `not`, so `not` must reject
    # them. An engine unable to complete the match must report an error too.
    invalid = _validate_json_under_stress(
        gts_session, gts_base_url, type_id, invalid_instance
    )
    _assert_explicit_validation_error(
        invalid,
        f"not must reject the instance or report a regex resource error in {keyword}; "
        "an execution failure must not be inverted into successful validation",
    )


@pytest.mark.parametrize(
    "keyword, dialect",
    [
        ("additionalProperties", _DRAFT_07),
        ("unevaluatedProperties", _DRAFT_2020_12),
    ],
    ids=["additionalProperties", "unevaluatedProperties"],
)
def test_property_classification_matches_under_stress(
    gts_session, gts_base_url, keyword, dialect
):
    """Bound the regex match used to classify keys as additional or unevaluated."""
    # The keyword precedes patternProperties so an implementation that
    # evaluates keywords in schema order classifies the key first, before a
    # bounded patternProperties match can fail the instance.
    type_id = _register_regexp_type(
        gts_session,
        gts_base_url,
        f"{keyword.lower()}_resource_limits",
        {
            keyword: False,
            "patternProperties": {_AMBIGUOUS_PATTERN: {"type": "integer"}},
        },
        dialect=dialect,
    )
    long_key = "a" * 64 + "!"
    # Matching keys with integer values are evaluated, not additional. Treating
    # the long key as a non-match would reject it through the closed object.
    for key in ("aaaa!", long_key):
        valid = _validate_json_under_stress(
            gts_session, gts_base_url, type_id, {key: 1}
        )
        assert valid["ok"] is True, (key, valid)

    # The key matches the pattern, so its value must be an integer. Whether the
    # engine completes the match or reports a resource error, the instance is
    # rejected within the limit.
    invalid = _validate_json_under_stress(
        gts_session, gts_base_url, type_id, {long_key: "not-an-integer"}
    )
    _assert_explicit_validation_error(
        invalid,
        f"{keyword} and patternProperties must reject the wrong value type or "
        "report a regex resource error",
    )


@pytest.mark.parametrize(
    "keyword",
    ["items", "patternProperties", "additionalProperties", "unevaluatedProperties"],
)
@pytest.mark.parametrize(
    "lengths, count",
    [(range(4, 8), 4), (range(64, 96), 1000)],
    ids=["short-control", "repeated-success-stress"],
)
def test_regex_repeated_success_completes(
    gts_session, gts_base_url, keyword, lengths, count
):
    """Many successful matches of an ambiguous expression complete in time.

    A backtracking engine whose per-match limit each long match exhausts
    reports an error here, while a linear engine completes. `count` is the
    number of array items; the property variants use one key per length.
    """
    if keyword == "items":
        body = {
            "properties": {
                "values": {"type": "array", "items": {"pattern": _AMBIGUOUS_PATTERN}}
            }
        }
        instance = {"values": ["a" * lengths[0] + "!"] * count}
    else:
        body = {"patternProperties": {_AMBIGUOUS_PATTERN: {"type": "integer"}}}
        if keyword != "patternProperties":
            # Classify keys before the patternProperties value checks.
            body = {keyword: False, **body}
        instance = {"a" * length + "!": 1 for length in lengths}
    type_id = _register_regexp_type(
        gts_session,
        gts_base_url,
        f"safe_success_{keyword.lower()}",
        body,
        dialect=_DRAFT_2020_12,
    )
    result = _validate_json_under_stress(gts_session, gts_base_url, type_id, instance)
    assert result["ok"] is True, result


# ---------------------------------------------------------------------------
# Schema positions
# ---------------------------------------------------------------------------


def _schema_positions(dialect, expression):
    """Schema positions of `expression` for `dialect`, mostly in inactive branches."""
    unsupported = {"pattern": expression}
    positions = {
        "not": {"not": {"not": unsupported}},
        "then": {"if": False, "then": unsupported},
        "else": {"if": True, "else": unsupported},
        "allof": {"allOf": [True, unsupported]},
        # An `if` without `then` or `else` has no effect on validation.
        "if": {"if": unsupported},
        "anyof": {"anyOf": [True, unsupported]},
        "oneof": {"oneOf": [True, {"not": unsupported}]},
        "definitions": {
            "definitions" if dialect == _DRAFT_07 else "$defs": {"unused": unsupported}
        },
        "traits": {"x-gts-traits-schema": {"properties": {"value": unsupported}}},
        # The trait schema refers into a container that is otherwise opaque.
        "traits_ref": {
            "x-gts-traits-schema": {"$ref": "#/customSchemas/traits"},
            "customSchemas": {"traits": {"properties": {"value": unsupported}}},
        },
        "pattern_properties_key": {
            "anyOf": [True, {"patternProperties": {expression: True}}]
        },
        "property_names": {"anyOf": [True, {"propertyNames": unsupported}]},
        "additional_properties": {"anyOf": [True, {"additionalProperties": unsupported}]},
        "items": {"anyOf": [True, {"items": unsupported}]},
        "contains": {"anyOf": [True, {"contains": unsupported}]},
        # A reference makes an unknown keyword's value a schema position, even
        # when the referencing branch never needs to be evaluated.
        "unknown_keyword_ref": {
            "anyOf": [True, {"$ref": "#/customSchemas/unused"}],
            "customSchemas": {"unused": unsupported},
        },
    }
    if dialect != _DRAFT_2020_12:
        positions["tuple_items"] = {"anyOf": [True, {"items": [unsupported]}]}
        positions["additional_items"] = {
            "anyOf": [True, {"items": [True], "additionalItems": unsupported}]
        }
    if dialect != _DRAFT_07:
        positions["unevaluated_items"] = {
            "anyOf": [True, {"unevaluatedItems": unsupported}]
        }
    if dialect == _DRAFT_07:
        positions["dependencies"] = {"dependencies": {"x": unsupported}}
    else:
        positions["dependent_schemas"] = {"dependentSchemas": {"x": unsupported}}
        positions["unevaluated_properties"] = {
            "anyOf": [True, {"unevaluatedProperties": unsupported}]
        }
    if dialect == _DRAFT_2020_12:
        positions["prefix_items"] = {"anyOf": [True, {"prefixItems": [unsupported]}]}
    return positions


_DIALECTS = (
    ("draft7", _DRAFT_07),
    ("draft2019", _DRAFT_2019_09),
    ("draft2020", _DRAFT_2020_12),
)
_POSITION_CASES = [
    (draft, dialect, position)
    for draft, dialect in _DIALECTS
    for position in _schema_positions(dialect, "")
]


@pytest.mark.parametrize(
    "label, expression",
    _PREFLIGHT_EXPRESSIONS,
    ids=[case[0] for case in _PREFLIGHT_EXPRESSIONS],
)
@pytest.mark.parametrize(
    "draft, dialect, position",
    _POSITION_CASES,
    ids=[f"{case[0]}-{case[2]}" for case in _POSITION_CASES],
)
def test_unsupported_regex_in_schema_positions(
    gts_session, gts_base_url, draft, dialect, position, label, expression
):
    """Every schema position is checked, at registration and on explicit validation.

    Whether instance validation must also fail after deferred registration
    when the expression sits in an inactive branch is not settled by README
    §11.0.1, so it is not asserted here.
    """
    body = _schema_positions(dialect, expression)[position]
    name = f"position_{draft}_{position}_{label}"
    _assert_schema_rejected(gts_session, gts_base_url, name, body, dialect)
    _assert_deferred_schema_rejected(
        gts_session, gts_base_url, f"deferred_{name}", body, dialect
    )


@pytest.mark.parametrize(
    "label, expression",
    _PREFLIGHT_EXPRESSIONS,
    ids=[case[0] for case in _PREFLIGHT_EXPRESSIONS],
)
def test_unsupported_regex_in_referenced_type(
    gts_session, gts_base_url, label, expression
):
    """A GTS `$ref` target's expressions are checked with the referencing type."""
    target = _assert_deferred_schema_rejected(
        gts_session, gts_base_url, f"ref_target_{label}", _pattern_body(expression)
    )
    # If the target was rejected eagerly, the reference no longer resolves,
    # which explicit validation must reject as well.
    target = target or _regexp_type_id(f"ref_target_{label}")
    body = {"anyOf": [True, {"$ref": f"gts://{target}"}]}
    _assert_schema_rejected(gts_session, gts_base_url, f"ref_holder_{label}", body)
    _assert_deferred_schema_rejected(
        gts_session, gts_base_url, f"deferred_ref_holder_{label}", body
    )


@pytest.mark.parametrize(
    "label, expression",
    _PREFLIGHT_EXPRESSIONS,
    ids=[case[0] for case in _PREFLIGHT_EXPRESSIONS],
)
def test_unsupported_regex_text_in_literal_data_is_not_checked(
    gts_session, gts_base_url, label, expression
):
    literal = {"pattern": expression}
    type_id = _register_regexp_type(
        gts_session,
        gts_base_url,
        f"literal_regex_text_{label}",
        {
            "default": literal,
            "examples": [literal],
            "customAnnotation": literal,
            "properties": {
                "pattern": {"type": "string"},
                "constValue": {"const": literal},
                "enumValue": {"enum": [literal]},
            },
        },
    )
    result = _validate_json(
        gts_session,
        gts_base_url,
        type_id,
        {"pattern": expression, "constValue": literal, "enumValue": literal},
    )
    assert result["ok"] is True, result


@pytest.mark.parametrize(
    "label, expression",
    _PREFLIGHT_EXPRESSIONS,
    ids=[case[0] for case in _PREFLIGHT_EXPRESSIONS],
)
@pytest.mark.parametrize(
    "keyword, instance",
    [
        ("prefixItems", {"value": ["zz"]}),
        ("dependentSchemas", {"value": {"x": 1}}),
    ],
)
def test_unsupported_regex_ignored_outside_declared_dialect(
    gts_session, gts_base_url, keyword, instance, label, expression
):
    """Draft-07 does not define these keywords, so their values are annotations."""
    unsupported = {"pattern": expression}
    body = {
        "prefixItems": {"prefixItems": [unsupported]},
        "dependentSchemas": {"dependentSchemas": {"x": unsupported}},
    }[keyword]
    type_id = _register_regexp_type(
        gts_session,
        gts_base_url,
        f"draft7_unknown_{keyword.lower()}_{label}",
        {"properties": {"value": body}},
    )
    result = _validate_json(gts_session, gts_base_url, type_id, instance)
    assert result["ok"] is True, result


@pytest.mark.parametrize(
    "label, expression",
    _PREFLIGHT_EXPRESSIONS,
    ids=[case[0] for case in _PREFLIGHT_EXPRESSIONS],
)
@pytest.mark.parametrize("form", ["direct", "negated"])
def test_deferred_registration_cannot_bypass_regex_check(
    gts_session, gts_base_url, form, label, expression
):
    # Ignoring the unsupported pattern would accept the direct case; treating it
    # as a non-match would make `not` accept the negated case.
    value_schema = {
        "direct": {"pattern": expression},
        "negated": {"not": {"pattern": expression}},
    }[form]
    type_id = _assert_deferred_schema_rejected(
        gts_session,
        gts_base_url,
        f"deferred_regex_{form}_{label}",
        _value_body(value_schema),
    )
    if type_id is None:
        return
    result = _validate_json(gts_session, gts_base_url, type_id, {"value": "zz"})
    _assert_explicit_validation_error(
        result, "unsupported regex at instance validation"
    )


def test_duration_pattern_compiles_in_trait_schema(gts_session, gts_base_url):
    type_id = "gts.x.test13regexp._.duration_trait.v1~"
    schema = {
        "$id": f"gts://{type_id}",
        "$schema": _DRAFT_07,
        "type": "object",
        "required": ["id"],
        "properties": {"id": {"type": "string"}},
        "x-gts-traits-schema": {
            "type": "object",
            "properties": {
                "duration": {
                    "type": "string",
                    "pattern": _DURATION_PATTERN,
                    "minLength": 2,
                },
            },
        },
    }
    registered = gts_session.post(
        f"{gts_base_url}/entities",
        json=schema,
        timeout=30,
    )
    assert registered.status_code == 200, registered.text
    result = _validate_type_schema_json(gts_session, gts_base_url, type_id)
    assert result["ok"] is True, result


# ---------------------------------------------------------------------------
# OP#13 - trait validation
# ---------------------------------------------------------------------------

_REGEX_FORMAT_TRAIT_TYPE_ID = "gts.x.test13.formats.regexsafe.v1~"
_REGEX_FORMAT_TRAIT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"regexValue": {"type": "string", "format": "regex"}},
}


class TestCaseOp13_Traits_RegexFormat(HttpRunner):
    """OP#13 asserts `format: regex` on trait values (README §11.0.1)."""

    config = Config("OP#13 - Regex format Trait Conformance").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            f"gts://{_REGEX_FORMAT_TRAIT_TYPE_ID}",
            {
                "type": "object",
                "x-gts-traits-schema": _REGEX_FORMAT_TRAIT_SCHEMA,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with regex trait format",
        ),
        *[
            _register_derived(
                f"gts://{_REGEX_FORMAT_TRAIT_TYPE_ID}x.test13._.regex_valid_{label}.v1~",
                f"gts://{_REGEX_FORMAT_TRAIT_TYPE_ID}",
                {
                    "type": "object",
                    "x-gts-traits": {"regexValue": pattern},
                },
                f"register derived with profile regex trait ({label})",
            )
            for label, pattern in _PROFILE_REGEX_STRINGS
        ],
        *[
            _validate_type_schema(
                f"{_REGEX_FORMAT_TRAIT_TYPE_ID}x.test13._.regex_valid_{label}.v1~",
                True,
                f"accept profile regex trait ({label})",
            )
            for label, _ in _PROFILE_REGEX_STRINGS
        ],
        *[
            _register_derived(
                f"gts://{_REGEX_FORMAT_TRAIT_TYPE_ID}x.test13._.regex_invalid_{label}.v1~",
                f"gts://{_REGEX_FORMAT_TRAIT_TYPE_ID}",
                {
                    "type": "object",
                    "x-gts-traits": {"regexValue": pattern},
                },
                f"register derived with out-of-profile regex trait ({label})",
            )
            for label, pattern in _REJECTED_REGEX_STRINGS
        ],
        *[
            _validate_type_schema(
                f"{_REGEX_FORMAT_TRAIT_TYPE_ID}x.test13._.regex_invalid_{label}.v1~",
                False,
                f"reject out-of-profile regex trait ({label})",
            )
            for label, _ in _REJECTED_REGEX_STRINGS
        ],
    ]
