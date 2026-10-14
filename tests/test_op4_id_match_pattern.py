"""OP#4 identifier pattern matching (README §10).

The vectors come from the shared test cases in shared_id_pattern_cases.py. A concrete
candidate matches when it is in M(pattern); a pattern candidate matches when
the filter covers it. A valid pair never reports an error, so a non-match
cannot pass because of a parse failure; an invalid string reports one.
"""

from .helpers.shared_cases import case_subtest
from .shared_id_pattern_cases import (
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


def test_concrete_candidate(gts_api, subtests):
    for case in MATCH_CASES:
        pattern, candidate, expect = case.values
        with case_subtest(
            subtests,
            case=case.id,
            pattern=pattern,
            candidate=candidate,
            expected=expect.matches,
        ):
            _assert_match(_match(gts_api, pattern, candidate), expect.matches)


def test_pattern_candidate_matches_by_coverage(gts_api, subtests):
    """One common identifier is not enough; the witness, selected by the
    candidate and not by the filter, shows why a candidate is not covered."""
    for case in COVERAGE_CASES:
        pattern, candidate, covered, witness = case.values
        with case_subtest(
            subtests,
            case=case.id,
            pattern=pattern,
            candidate=candidate,
            expected=covered,
            witness=witness,
        ):
            _assert_match(_match(gts_api, pattern, candidate), covered)
            if witness is not None:
                _assert_match(_match(gts_api, candidate, witness), True)
                _assert_match(_match(gts_api, pattern, witness), False)


def test_universal_pattern_matches_every_valid_pattern(gts_api, subtests):
    for case in VALID_PATTERNS:
        (value,) = case.values
        with case_subtest(subtests, case=case.id, candidate=value, expected=True):
            _assert_match(_match(gts_api, "gts.*", value), True)


def test_invalid_pattern_is_an_error(gts_api, subtests):
    for case in INVALID_PATTERNS:
        (value,) = case.values
        with case_subtest(subtests, case=case.id, pattern=value):
            _assert_invalid(_match(gts_api, value, _CONCRETE))


def test_invalid_candidate_is_an_error(gts_api, subtests):
    for case in INVALID_PATTERNS:
        (value,) = case.values
        with case_subtest(subtests, case=case.id, candidate=value):
            _assert_invalid(_match(gts_api, "gts.*", value))
