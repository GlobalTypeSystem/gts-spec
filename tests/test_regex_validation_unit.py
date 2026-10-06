"""Offline checks of the expectations in test_regex_validation.py.

The HTTP helpers are replaced by fake engines, and the real test functions are
called directly. The fakes are crude stand-ins built on Python `re` for the
expressions these tests use; they are not a GTS profile checker or an RE2
implementation.
"""

import re
import warnings

import pytest

from . import test_regex_validation as rv

pytestmark = pytest.mark.unit

_UNICODE_SPACE = "\t-\r \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000"
# Python `\w` lacks marks and Join_Control; enough for the probes used here.
_UNICODE_WORD = "\\w\u0300-\u036f\u200c\u200d"
# Class contents of the lowercase shorthands; uppercase ones are complements.
_REFERENCE_SETS = {"d": "0-9", "w": "A-Za-z0-9_", "s": "\t\n\f\r "}
# Tokens of constructs outside the draft profile, for the fake support check.
_EXCLUDED_TOKENS = (
    "(?=", "(?!", "(?<", "\\1", "\\k", "\\u", "\\Q", "(?U", "(?i", "\\z",
    "\\x{", "[:", "\\C", "(?>", "++", "**", "\\p", "\\b", "\\B", "\\@", "\\0",
)


def _translate(pattern, dot, end, sets, class_sets=None):
    """Rewrites `.`, `$`, and shorthands for Python `re`.

    Inside classes, lowercase shorthands use `class_sets` (default `sets`);
    uppercase ones keep Python's meaning, which no matching probe relies on.
    """
    class_sets = sets if class_sets is None else class_sets
    out, in_class, index = [], False, 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\" and index + 1 < len(pattern):
            escaped = pattern[index + 1]
            if in_class and escaped in class_sets:
                out.append(class_sets[escaped])
            elif not in_class and escaped.lower() in sets:
                negate = "^" if escaped.isupper() else ""
                out.append(f"[{negate}{sets[escaped.lower()]}]")
            else:
                out.append(char + escaped)
            index += 2
            continue
        if in_class:
            in_class = char != "]"
            out.append(char)
        elif char == "[":
            in_class = True
            out.append(char)
        elif char == ".":
            out.append(dot)
        elif char == "$":
            out.append(end)
        else:
            out.append(char)
        index += 1
    return "".join(out)


class FakeEngine:
    """Reference-like behavior: GTS RE2 results for the test expressions."""

    dot = "[^\n]"
    end = r"\Z"
    sets = _REFERENCE_SETS
    class_sets = None
    excluded = _EXCLUDED_TOKENS

    def supports(self, expression):
        # The fake neither computes the support bounds nor applies the
        # spelling rules; it rejects the suite's fixtures for them by value.
        if expression in {expr for _, expr in rv._OUTSIDE_BOUNDS + rv._AMBIGUOUS_SPELLINGS}:
            return False
        # An escaped backslash does not start an escape.
        unescaped = expression.replace("\\\\", "\0")
        if any(token in unescaped for token in self.excluded):
            return False
        try:
            self._compile(expression)
        except re.error:
            return False
        return True

    def search(self, pattern, probe):
        return self._compile(pattern).search(probe) is not None

    def _compile(self, expression):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            return re.compile(
                _translate(
                    expression, self.dot, self.end, self.sets, self.class_sets
                )
            )


class RejectsDigitShorthand(FakeEngine):
    """Consistently rejects `\\d` in every path."""

    def supports(self, expression):
        return "\\d" not in expression and super().supports(expression)


class AcceptsLookahead(FakeEngine):
    """Consistently accepts lookahead in every path."""

    excluded = tuple(t for t in _EXCLUDED_TOKENS if t not in ("(?=", "(?!"))


class PythonEnd(FakeEngine):
    """Python `$`, which also matches before a final newline."""

    end = "$"


class EcmaDot(FakeEngine):
    """ECMA-262 `.`, which also excludes CR, U+2028, and U+2029."""

    dot = "[^\n\r\u2028\u2029]"


class UnicodeSpace(FakeEngine):
    """`\\s` is Unicode White_Space, as in Rust's default mode."""

    sets = {**_REFERENCE_SETS, "s": _UNICODE_SPACE}


class UnicodeSpaceOutsideClasses(UnicodeSpace):
    """Applies the declared `\\s` only outside classes."""

    class_sets = _REFERENCE_SETS


class UnicodeWord(FakeEngine):
    """`\\w` approximates the UTS #18 word set; `\\d` stays ASCII."""

    sets = {**_REFERENCE_SETS, "w": _UNICODE_WORD}


class PythonWord(FakeEngine):
    """Python's Unicode `\\w`, which lacks marks and Join_Control."""

    sets = {**_REFERENCE_SETS, "w": "\\w"}


def _install(monkeypatch, engine, path_engines=None):
    """Routes the HTTP helpers of `rv` to `engine`, per path if given."""
    path_engines = path_engines or {}

    def format_support(session, url, format_types, trait_bases, name, expression):
        return {
            "format": engine.supports(expression),
            "trait_format": engine.supports(expression),
        }

    def register_paths(session, url, name, pattern):
        return {
            path: (pattern, pattern)
            if path_engines.get(path, engine).supports(pattern)
            else (None, None)
            for path in rv._SCHEMA_PATHS
        }

    def path_verdicts(session, url, paths, name, probe):
        pattern = paths["pattern"][0]
        return {
            path: path_engines.get(path, engine).search(pattern, probe)
            for path in rv._VERDICT_PATHS
        }

    monkeypatch.setattr(rv, "_format_support", format_support)
    monkeypatch.setattr(rv, "_register_paths", register_paths)
    monkeypatch.setattr(rv, "_path_verdicts", path_verdicts)


def _support(category, label, expression):
    rv.test_regex_support(None, None, None, None, category, label, expression)


def _match(label, pattern, matches, non_matches):
    rv.test_reference_matching(None, None, None, None, label, pattern, matches, non_matches)


def _difference(case):
    rv.test_matching_differences_follow_declaration(None, None, *case)


def _support_case(label):
    return next(case for case in rv._SUPPORT_CASES if case[1] == label)


def _match_case(label):
    return next(case for case in rv._MATCH_CASES if case[0] == label)


# --- Positive control --------------------------------------------------------


def test_reference_like_engine_passes_every_expectation(monkeypatch):
    _install(monkeypatch, FakeEngine())
    for case in rv._SUPPORT_CASES:
        _support(*case)
    for case in rv._MATCH_CASES:
        _match(*case)
    monkeypatch.setattr(rv, "_DECLARED_BEHAVIOR", {})
    for case in rv._DIFFERENCE_CASES:
        _difference(case)


# --- Scenarios that path agreement alone used to accept ---------------------


def test_consistent_rejection_of_digit_shorthand_fails(monkeypatch):
    _install(monkeypatch, RejectsDigitShorthand())
    with pytest.raises(AssertionError, match="must be supported"):
        _support(*_support_case("shorthand_classes"))
    with pytest.raises(AssertionError, match="must be supported"):
        _match(*_match_case("digit_ascii"))


def test_consistent_acceptance_of_lookahead_fails(monkeypatch):
    _install(monkeypatch, AcceptsLookahead())
    for label in ("lookahead", "negative_lookahead"):
        with pytest.raises(AssertionError, match="must be rejected"):
            _support(*_support_case(label))


def test_python_end_before_final_newline_fails(monkeypatch):
    _install(monkeypatch, PythonEnd())
    with pytest.raises(AssertionError, match="must not match") as raised:
        _match(*_match_case("multiline_off"))
    # pytest's assertion rewriting prints the probe with a real newline.
    message = str(raised.value)
    assert "'abc\n" in message or repr("abc\n") in message, message


def test_disagreeing_support_fails(monkeypatch):
    _install(monkeypatch, FakeEngine(), {"trait": AcceptsLookahead()})
    with pytest.raises(AssertionError, match="paths disagree on support"):
        _support(*_support_case("lookahead"))


# --- Declared matching differences ------------------------------------------


def test_ecma_dot_fails(monkeypatch):
    _install(monkeypatch, EcmaDot())
    with pytest.raises(AssertionError, match="must match"):
        _match(*_match_case("dot_line_terminators"))


def _difference_case(label):
    return next(case for case in rv._DIFFERENCE_CASES if case[1] == label)


def test_undeclared_difference_requires_reference(monkeypatch):
    _install(monkeypatch, UnicodeSpace())
    monkeypatch.setattr(rv, "_DECLARED_BEHAVIOR", {})
    with pytest.raises(AssertionError, match="must not match"):
        _difference(_difference_case("space_nbsp"))


def test_declared_deviation_passes(monkeypatch):
    _install(monkeypatch, UnicodeSpace())
    monkeypatch.setattr(rv, "_DECLARED_BEHAVIOR", {"space": "unicode"})
    for case in rv._DIFFERENCE_CASES:
        if case[0] == "space":
            _difference(case)


def test_declared_deviation_must_match_server(monkeypatch):
    _install(monkeypatch, FakeEngine())
    monkeypatch.setattr(rv, "_DECLARED_BEHAVIOR", {"space": "unicode"})
    with pytest.raises(AssertionError, match="must match"):
        _difference(_difference_case("space_nbsp"))


def test_deviation_ignored_inside_classes_fails(monkeypatch):
    _install(monkeypatch, UnicodeSpaceOutsideClasses())
    monkeypatch.setattr(rv, "_DECLARED_BEHAVIOR", {"space": "unicode"})
    _difference(_difference_case("space_nbsp"))
    with pytest.raises(AssertionError, match="must match"):
        _difference(_difference_case("class_space_nbsp"))


def test_declared_word_deviation_is_independent_of_digit(monkeypatch):
    _install(monkeypatch, UnicodeWord())
    monkeypatch.setattr(rv, "_DECLARED_BEHAVIOR", {"word": "unicode"})
    for case in rv._DIFFERENCE_CASES:
        if case[0] == "word":
            _difference(case)
    for label in ("digit_arabic_indic", "class_non_digit_arabic_indic"):
        _difference(_difference_case(label))


def test_python_word_set_fails_word_declaration(monkeypatch):
    _install(monkeypatch, PythonWord())
    monkeypatch.setattr(rv, "_DECLARED_BEHAVIOR", {"word": "unicode"})
    for label in ("word_combining_mark", "word_zero_width_joiner"):
        with pytest.raises(AssertionError, match="must match"):
            _difference(_difference_case(label))


def test_declared_behavior_parsing():
    assert rv._parse_declared_behavior("") == {}
    assert rv._parse_declared_behavior('{"space": "unicode", "digit": "reference"}') == {
        "space": "unicode",
        "digit": "reference",
    }
    for text in ('["space"]', '{"case": "reference"}', '{"dot": "lf_only"}', '{"space": "re2"}'):
        with pytest.raises(ValueError):
            rv._parse_declared_behavior(text)


# --- Table invariants --------------------------------------------------------


def test_difference_cases_cover_every_permitted_behavior():
    for construct, label, _, _, _, alternatives in rv._DIFFERENCE_CASES:
        assert set(alternatives) == set(rv._PERMITTED_BEHAVIORS[construct]), label
    assert {case[0] for case in rv._DIFFERENCE_CASES} == set(rv._PERMITTED_BEHAVIORS)


def test_labels_are_unique_and_usable_in_identifiers():
    # Each table prefixes its type names differently, so labels need only be
    # unique within a table.
    for labels in (
        [case[1] for case in rv._SUPPORT_CASES],
        [case[0] for case in rv._MATCH_CASES],
        [case[1] for case in rv._DIFFERENCE_CASES],
        [case[0] for case in rv._PREFLIGHT_EXPRESSIONS],
    ):
        assert len(labels) == len(set(labels)), labels
        for label in labels:
            assert re.fullmatch("[a-z_][a-z0-9_]*", label), label


def test_unicode_escape_case_is_a_regex_escape():
    # The regex source is backslash, "u", "0041"; the literal "A" is permitted.
    escape = chr(0x5C) + "u0041"
    assert rv._UNICODE_REGEX_ESCAPE == escape
    assert [ord(c) for c in rv._UNICODE_REGEX_ESCAPE] == [0x5C, 0x75, 0x30, 0x30, 0x34, 0x31]
    assert dict(rv._OUTSIDE_COMMON_SYNTAX)["unicode_escape"] == escape
    assert dict(rv._PREFLIGHT_EXPRESSIONS)["not_re2"] == escape
    assert "A" not in {expr for _, expr in rv._REJECTED_REGEX_STRINGS}


def test_escape_sensitive_fixture_values():
    # Literal U+2028 and U+2029 after JSON decoding; regex escapes for LF and CR.
    assert rv._ECMA_DOT_PATTERN == (
        "^P[^" + chr(0x5C) + "n" + chr(0x5C) + "r" + chr(0x2028) + chr(0x2029) + "]+"
    )
    probes = {case[1]: case[3] for case in rv._DIFFERENCE_CASES}
    assert [ord(probes[label]) for label in (
        "digit_arabic_indic", "space_vertical_tab", "space_nbsp", "space_bom",
        "space_next_line",
    )] == [0x661, 0x0B, 0xA0, 0xFEFF, 0x85]
    dot_matches = _match_case("dot_line_terminators")[2]
    assert [ord(probe) for probe in dot_matches] == [0x0D, 0x2028, 0x2029]
    assert dict(rv._EXCLUDED_BY_DRAFT)["word_boundary"] == chr(0x5C) + "ba" + chr(0x5C) + "b"


def test_regex_sources_contain_no_decoded_escapes():
    """A lost raw-string prefix would turn regex escapes into control characters."""
    sources = [case[2] for case in rv._SUPPORT_CASES]
    sources += [case[1] for case in rv._MATCH_CASES]
    sources += [case[2] for case in rv._DIFFERENCE_CASES]
    sources += [expr for _, expr in rv._PREFLIGHT_EXPRESSIONS]
    for source in sources:
        assert not any(ord(c) < 0x20 for c in source), repr(source)


_BOUND_QUANTIFIER = re.compile(r"\{(\d+)(,(\d*))?\}\??|[*+?]\??")


def _bounds(expression):
    """Expanded length, product, group depth, and counts (README §11.0.1).

    A small calculator for the suite's fixtures, not a profile checker: it
    assumes well-formed input and reads alternation and anchors as one-character
    items.
    """
    pos, counts = 0, []

    def sequence(depth):
        nonlocal pos
        length, product, deepest = 0, 1, depth
        while pos < len(expression) and expression[pos] != ")":
            start = pos
            atom_product, atom_depth = 1, depth
            if expression[pos] == "(":
                pos += 3 if expression.startswith("(?:", pos) else 1
                opening = pos - start
                inner_length, atom_product, atom_depth = sequence(depth + 1)
                pos += 1
                atom_length = opening + inner_length + 1
            elif expression[pos] == "[":
                pos += 2 if expression.startswith("[^", pos) else 1
                while expression[pos] != "]":
                    pos += 2 if expression[pos] == "\\" else 1
                pos += 1
                atom_length = pos - start
            elif expression.startswith("\\x", pos):
                pos += 4
                atom_length = 4
            else:
                pos += 2 if expression[pos] == "\\" else 1
                atom_length = pos - start
            quantifier = _BOUND_QUANTIFIER.match(expression, pos)
            if quantifier and quantifier[0].startswith("{"):
                lower = int(quantifier[1])
                upper = lower if quantifier[2] is None else (
                    int(quantifier[3]) if quantifier[3] else None
                )
                counts.extend(int(c) for c in (quantifier[1], quantifier[3]) if c)
                copies = lower + 1 if upper is None else max(upper, 1)
                atom_length = len(quantifier[0]) + copies * atom_length
                atom_product *= (lower if upper is None else upper) or 1
            elif quantifier:
                atom_length += len(quantifier[0])
            if quantifier:
                pos = quantifier.end()
            length += atom_length
            product = max(product, atom_product)
            deepest = max(deepest, atom_depth)
        return length, product, deepest

    return (*sequence(0), counts)


def _bound_violations(expression):
    length, product, depth, counts = _bounds(expression)
    return {
        name
        for name, exceeded in (
            ("length", length > 4096),
            ("product", product > 1000),
            ("count", any(count > 1000 for count in counts)),
            ("depth", depth > 32),
        )
        if exceeded
    }


def test_bounds_calculator_matches_documented_examples():
    assert _bounds("a{1000}") == (1006, 1000, 0, [1000])
    assert _bounds("(?:ab){1000}") == (6006, 1000, 1, [1000])
    assert _bounds(rv._COUNTED_REPETITION_PATTERN)[:2] == (3512, 500)
    # A hex escape is one atom; braces inside a class are not counts.
    assert _bounds(r"\x41{1000}")[0] == 4006
    assert not _bound_violations("[{1001}]")


def test_bound_fixtures_are_on_the_intended_side():
    for label, expression in rv._PROFILE_REGEX_STRINGS:
        assert not _bound_violations(expression), label
    assert not _bound_violations(rv._COUNTED_REPETITION_PATTERN)
    for label, expression in rv._OUTSIDE_BOUNDS:
        assert _bound_violations(expression), label
    # These isolate a single rule.
    isolated = {
        "expanded_length_4097": {"length"},
        "astral_4097": {"length"},
        "nested_upper_count_1010": {"product"},
        "zero_count_product_2000": {"product"},
        "nested_repeat_2000": {"product"},
        "group_nesting_33": {"depth"},
    }
    for label, expression in rv._OUTSIDE_BOUNDS:
        if label in isolated:
            assert _bound_violations(expression) == isolated[label], label


def test_rejected_and_profile_sets_are_disjoint():
    rejected = {expr for _, expr in rv._REJECTED_REGEX_STRINGS}
    profile = {expr for _, expr in rv._PROFILE_REGEX_STRINGS}
    assert not rejected & profile
    for _, expr in rv._PREFLIGHT_EXPRESSIONS:
        assert expr in rejected


# --- Local references --------------------------------------------------------


def _local_refs(node):
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#"):
            yield ref
        for value in node.values():
            yield from _local_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from _local_refs(value)


def _resolve_pointer(root, ref):
    node = root
    for token in ref[1:].split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        assert isinstance(node, dict) and token in node, (ref, token)
        node = node[token]
    return node


def _posted_root(body, dialect):
    # The document that _post_schema sends for `body`.
    return {"$id": "gts://gts.x.test6regexp._.ref_check.v1~", "$schema": dialect, "type": "object", **body}


def test_ref_definition_refs_resolve_from_root():
    """`not` must not move definitions away from a root-relative reference."""
    (body, negated), dialect = rv._path_bodies("^a$")["ref_definition"]
    for schema in (body, negated):
        root = _posted_root(schema, dialect)
        refs = list(_local_refs(root))
        assert refs, schema
        for ref in refs:
            assert _resolve_pointer(root, ref)["pattern"] == "^a$", ref


def test_every_posted_local_ref_resolves_from_root():
    for path, ((body, negated), dialect) in rv._path_bodies("^a$").items():
        for schema in (body, negated):
            root = _posted_root(schema, dialect)
            for ref in _local_refs(root):
                _resolve_pointer(root, ref)
    for _, dialect in rv._DIALECTS:
        for position, body in rv._schema_positions(dialect, "a(?=b)").items():
            root = _posted_root(body, dialect)
            for ref in _local_refs(root):
                target = _resolve_pointer(root, ref)
                assert "a(?=b)" in repr(target), (position, ref)


def test_traits_ref_position_reaches_custom_container():
    body = rv._schema_positions(rv._DRAFT_07, "a(?=b)")["traits_ref"]
    root = _posted_root(body, rv._DRAFT_07)
    target = _resolve_pointer(root, body["x-gts-traits-schema"]["$ref"])
    assert target["properties"]["value"] == {"pattern": "a(?=b)"}
