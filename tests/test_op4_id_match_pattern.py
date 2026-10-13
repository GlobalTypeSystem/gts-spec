"""OP#4 identifier pattern matching (README §10).

The vectors come from the shared corpus in id_pattern_corpus.py. A concrete
candidate matches when it is in M(pattern); a pattern candidate matches when
the filter covers it. A valid pair never reports an error, so a non-match
cannot pass because of a parse failure; an invalid string reports one.
"""

import pytest

from .id_pattern_corpus import (
    COVERAGE_CASES,
    INVALID_PATTERNS,
    MATCH_CASES,
    VALID_PATTERNS,
)

_CONCRETE = "gts.x.core.events.type.v1~"


def _match(api, pattern, candidate):
    return api.request(
        "GET",
        "/match-id-pattern",
        params={"pattern": pattern, "candidate": candidate},
    )


def _assert_match(result, expected):
    assert result["match"] is expected, result
    assert not result.get("error"), result


def _assert_invalid(result):
    assert result["match"] is False, result
    assert result.get("error"), result


@pytest.mark.parametrize("pattern,candidate,expect", MATCH_CASES)
def test_concrete_candidate(gts_api, pattern, candidate, expect):
    _assert_match(_match(gts_api, pattern, candidate), expect.matches)


@pytest.mark.parametrize("pattern,candidate,covered,witness", COVERAGE_CASES)
def test_pattern_candidate_matches_by_coverage(
    gts_api, pattern, candidate, covered, witness
):
    """One common identifier is not enough; the witness, selected by the
    candidate and not by the filter, shows why a candidate is not covered."""
    _assert_match(_match(gts_api, pattern, candidate), covered)
    if witness is not None:
        _assert_match(_match(gts_api, candidate, witness), True)
        _assert_match(_match(gts_api, pattern, witness), False)


@pytest.mark.parametrize("value", VALID_PATTERNS)
def test_universal_pattern_matches_every_valid_pattern(gts_api, value):
    _assert_match(_match(gts_api, "gts.*", value), True)


@pytest.mark.parametrize("value", INVALID_PATTERNS)
def test_invalid_pattern_is_an_error(gts_api, value):
    _assert_invalid(_match(gts_api, value, _CONCRETE))


@pytest.mark.parametrize("value", INVALID_PATTERNS)
def test_invalid_candidate_is_an_error(gts_api, value):
    _assert_invalid(_match(gts_api, "gts.*", value))
