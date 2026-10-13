"""Offline checks of the value lists in test_x_gts_pattern_ref.py.

The recognizer below transcribes the `gts-id-pattern` grammar of README §10
and the identifier grammar of §2.3, with the length and u32 version limits. It guards
the test data against mistakes; it is not a GTS implementation.
"""

import re

import pytest

from . import test_x_gts_pattern_ref as patterns

pytestmark = pytest.mark.unit

_TOKEN = r"[a-z_][a-z0-9_]*"
_NUMBER = r"(?:0|[1-9][0-9]*)"
_SEGMENT = rf"{_TOKEN}\.{_TOKEN}\.{_TOKEN}\.{_TOKEN}\.v{_NUMBER}(?:\.{_NUMBER})?"
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_IDENTIFIER = (
    rf"gts\.{_SEGMENT}"
    rf"(?:(?:~{_SEGMENT})*~|(?:~{_SEGMENT})+|(?:~{_SEGMENT})*~{_UUID})"
)
_SEGMENT_PREFIX = (
    rf"{_TOKEN}\.(?:{_TOKEN}\.(?:{_TOKEN}\.(?:{_TOKEN}\.(?:v(?:{_NUMBER}\.)?)?)?)?)?"
)
_WILDCARD_PATTERN = rf"gts\.(?:{_SEGMENT}~)*(?:{_SEGMENT_PREFIX})?\*"
_GTS_ID_PATTERN = re.compile(rf"(?:{_IDENTIFIER}|{_WILDCARD_PATTERN})", re.ASCII)


def _is_gts_id_pattern(value):
    if len(value) > 1024 or _GTS_ID_PATTERN.fullmatch(value) is None:
        return False
    for segment in value[4:].split("~"):
        tokens = segment.split(".")
        if len(tokens) >= 5:
            versions = [tokens[4].removeprefix("v"), *tokens[5:]]
            if any(
                number.isdecimal() and int(number) > 4294967295 for number in versions
            ):
                return False
    return True


@pytest.mark.parametrize("value", patterns.VALID_PATTERNS)
def test_valid_patterns_match_grammar(value):
    assert _is_gts_id_pattern(value)


@pytest.mark.parametrize("value", patterns.INVALID_PATTERNS)
def test_invalid_patterns_do_not_match_grammar(value):
    assert not _is_gts_id_pattern(value)


def test_length_boundary():
    assert len(patterns._LONGEST_PATTERN) == 1024


@pytest.mark.parametrize(
    "pattern,completion,witness",
    [
        (
            patterns._EMPTY_VENDOR_PATTERN,
            patterns._EMPTY_VENDOR_COMPLETION,
            patterns._VENDOR_WITNESS,
        ),
        (
            patterns._EMPTY_VERSION_PATTERN,
            patterns._EMPTY_VERSION_COMPLETION,
            patterns._VERSION_WITNESS,
        ),
    ],
    ids=["vendor", "version_marker"],
)
def test_empty_selection_boundary(pattern, completion, witness):
    """The stated shortest completion of the empty pattern exceeds 1024
    characters; the neighbouring pattern's witness has exactly 1024."""
    assert _is_gts_id_pattern(pattern)
    assert completion.startswith(pattern[:-1])
    assert len(completion) == 1025
    assert not _is_gts_id_pattern(completion)
    assert len(witness) == 1024
    assert _is_gts_id_pattern(witness)


@pytest.mark.parametrize("operand,value", patterns.COVERED_CASES)
def test_covered_vectors_are_syntactically_valid(operand, value):
    """Check vector spelling, without computing the expected coverage."""
    assert _is_gts_id_pattern(operand)
    assert _is_gts_id_pattern(value)


@pytest.mark.parametrize("operand,value,witness", patterns.UNCOVERED_CASES)
def test_uncovered_vectors_are_syntactically_valid(operand, value, witness):
    """Check vector spelling; the witness is a concrete identifier."""
    assert _is_gts_id_pattern(operand)
    assert _is_gts_id_pattern(value)
    assert "*" not in witness
    assert _is_gts_id_pattern(witness)
