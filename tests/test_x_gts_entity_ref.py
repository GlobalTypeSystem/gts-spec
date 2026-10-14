"""Conformance tests for x-gts-type-ref and x-gts-instance-ref (GTS 0.17).

README §9.6.1, §9.6.3, §11.0 and ADR-0008. The operand is the keyword's value
in the schema; the candidate is the string being validated. §10 matching uses
the shared test cases in shared_id_pattern_cases.py. Combinators, array schemas, local
references and registry modes on concrete fields are covered in
test_refimpl_x_gts_ref.py.

Structural checks (operand validity, candidate syntax, kind, matching) are
isolated with `gts-ref-validation=none`. Negative cases are paired with a
control that differs only in the tested aspect: schema-error controls use a
registered, valid operand target, and wrong-kind candidates are registered and
valid. The transient instance endpoints take no reference policy, so their
kind, matching and self-reference cases use registered, valid targets and
have the same expected results under every policy.
"""

from types import SimpleNamespace

import pytest

from .helpers.shared_cases import case_subtest
from .helpers.http_client import GtsTestAPI
from .shared_id_pattern_cases import COVERAGE_CASES, INVALID_PATTERNS, MATCH_CASES

TYPE_REF = "x-gts-type-ref"
INSTANCE_REF = "x-gts-instance-ref"
KEYWORDS = (TYPE_REF, INSTANCE_REF)
MODES = ("none", "any-present", "any-valid")
UUID = "7a1d2f34-5678-49ab-9012-abcdef123456"


def _holder(ref_schema):
    return {"type": "object", "properties": {"ref": ref_schema}}


def _is_type_id(gts_id):
    return gts_id.endswith("~")


def _register_type(api, dialect, type_id, schema=None, **kwargs):
    return api.register(
        None, schema or {"type": "object"}, dialect, type_id=type_id, **kwargs
    )


def _register_derived(api, dialect, base, name, **kwargs):
    return _register_type(
        api,
        dialect,
        api.derived_type_id(base, name),
        {"type": "object", "allOf": [{"$ref": "gts://" + base}]},
        **kwargs,
    )


def _register_instance_id(api, type_id, instance_id):
    api.request(
        "POST",
        "/entities",
        params={"validate": "true"},
        json={"id": instance_id, "type": type_id},
    )
    return instance_id


def _register_uuid_instance(api, type_id):
    return _register_instance_id(api, type_id, type_id + UUID)


def _targets(api, dialect):
    """Valid registered entities around the operand type `t`."""
    t = _register_type(api, dialect, api.type_id("target"))
    d = _register_derived(api, dialect, t, "derived")
    tm = _register_type(api, dialect, api.type_id("target", "1.0"))
    other = _register_type(api, dialect, api.type_id("other"))
    return SimpleNamespace(
        t=t,
        d=d,
        tm=tm,
        itm=api.register_instance(tm, {}, validate=True),
        t2=_register_type(api, dialect, api.type_id("target", "2")),
        other=other,
        it=api.register_instance(t, {}, validate=True),
        idv=api.register_instance(d, {}, validate=True),
        u=_register_uuid_instance(api, t),
        oi=api.register_instance(other, {}, validate=True),
    )


def _check_payloads(api, holder, expectations, mode):
    """Registers each payload as an instance of `holder` and checks its verdict."""
    for index, (payload, valid) in enumerate(expectations):
        instance_id = api.register_instance(holder, payload, name=f"c{index}")
        try:
            api.check_instance(instance_id, valid=valid, mode=mode)
        except AssertionError as error:
            raise AssertionError(
                f"payload {payload!r} expected valid={valid}: {error}"
            ) from None


def _check_refs(api, holder, expectations, mode="none"):
    _check_payloads(
        api, holder, [({"ref": ref}, valid) for ref, valid in expectations], mode
    )


def _assert_schema_error(api, dialect, schema, control):
    """`schema` is a schema error on every path; `control` is valid.

    The control differs only in the tested reference and uses a registered,
    valid operand target, so it is valid under every reference policy,
    including the default policy of POST /validate-json.
    """
    api.register("control", control, dialect)
    api.check_transient_schema("control_transient", control, dialect, valid=True)
    api.check_transient_schema("transient", schema, dialect, valid=False)
    _assert_stored_schema_error(api, dialect, schema)


def _assert_stored_schema_error(api, dialect, schema):
    """Registration with validation rejects `schema` without registry lookup;
    a schema stored without validation fails later validation."""
    api.register("rejected", schema, dialect, mode="none", status=422)
    deferred = api.register_deferred("deferred", schema, dialect)
    if deferred is not None:
        # Storing without validation does not establish validity (§9.6.3).
        api.check_type_schema(deferred, valid=False, mode="none")
        instance_id = api.register_instance(deferred, {})
        api.check_instance(instance_id, valid=False, mode="none")


# ---------------------------------------------------------------------------
# Operands
# ---------------------------------------------------------------------------

def _long_type_id(prefix, length):
    """A well-formed Type ID of exactly `length` characters."""
    type_id = prefix + "." + "a" * (length - len(prefix) - len(".v1~") - 1) + ".v1~"
    assert len(type_id) == length
    return type_id

VALID_OPERANDS = (
    pytest.param(lambda r: r.t, id="concrete_type"),
    pytest.param(lambda r: r.t + "*", id="chain_wildcard"),
    pytest.param(lambda r: r.t[:-1] + ".*", id="explicit_minor_wildcard"),
    pytest.param(lambda r: r.t + "x.pytest.*", id="derived_segment_wildcard"),
    pytest.param(lambda r: r.prefix + ".*", id="namespace_wildcard"),
    pytest.param(lambda r: "gts.*", id="universal"),
    pytest.param(lambda r: "/$id", id="self"),
    pytest.param(lambda r: _long_type_id(r.prefix, 1024), id="length_1024"),
)
# A concrete Instance ID selects only instances (ADR-0008).
INSTANCE_OPERANDS = (
    pytest.param(lambda r: r.it, id="concrete_instance"),
    pytest.param(lambda r: r.it + ".0", id="concrete_instance_explicit_minor"),
    pytest.param(lambda r: r.u, id="uuid_instance"),
)
# Invalid pattern strings are in the shared test cases
# (test_invalid_pattern_operand_is_schema_error); these are the other forms.
INVALID_OPERANDS = (
    pytest.param(lambda r: "/properties/anchor", id="property_pointer"),
    pytest.param(lambda r: "/" + r.t, id="slash_type_id"),
    pytest.param(lambda r: "/$id/", id="extended_self_pointer"),
    pytest.param(lambda r: "./$id", id="dot_slash_self"),
    pytest.param(lambda r: "$id", id="bare_id"),
    pytest.param(lambda r: "/", id="root_pointer"),
    pytest.param(lambda r: 42, id="number"),
    pytest.param(lambda r: None, id="null"),
    pytest.param(lambda r: True, id="boolean"),
    pytest.param(lambda r: [r.t], id="array"),
    pytest.param(lambda r: {"kind": "type", "target": r.t}, id="object"),
)


def _operand_targets(api, dialect):
    t = _register_type(api, dialect, api.type_id("target"))
    it = api.register_instance(t, {}, validate=True)
    return SimpleNamespace(
        t=t, it=it, u=_register_uuid_instance(api, t), prefix=api.id_prefix
    )


def _operand_schema(keyword, operand):
    return {
        "type": "object",
        "properties": {
            "anchor": {"type": "string"},
            "ref": {"type": "string", keyword: operand},
        },
    }


@pytest.mark.parametrize("keyword", KEYWORDS)
@pytest.mark.parametrize("operand", VALID_OPERANDS)
def test_valid_operand_is_accepted(gts_api, schema_dialect, keyword, operand):
    api = gts_api
    targets = _operand_targets(api, schema_dialect)
    holder = api.register(
        "holder",
        _operand_schema(keyword, operand(targets)),
        schema_dialect,
        mode="none",
    )
    api.check_type_schema(holder, valid=True, mode="none")


@pytest.mark.parametrize("operand", INSTANCE_OPERANDS)
def test_instance_operand_is_valid_only_for_instance_ref(
    gts_api, schema_dialect, operand
):
    """The operand asymmetry: a concrete Instance ID cannot satisfy a type
    reference, so it is a schema error there, and valid for an instance
    reference."""
    api = gts_api
    targets = _operand_targets(api, schema_dialect)
    holder = api.register(
        "holder",
        _operand_schema(INSTANCE_REF, operand(targets)),
        schema_dialect,
        mode="none",
    )
    api.check_type_schema(holder, valid=True, mode="none")
    _assert_schema_error(
        api,
        schema_dialect,
        _operand_schema(TYPE_REF, operand(targets)),
        control=_operand_schema(TYPE_REF, targets.t),
    )


@pytest.mark.parametrize("keyword", KEYWORDS)
@pytest.mark.parametrize("operand", INVALID_OPERANDS)
def test_invalid_operand_is_schema_error(gts_api, schema_dialect, keyword, operand):
    api = gts_api
    targets = _operand_targets(api, schema_dialect)
    _assert_schema_error(
        api,
        schema_dialect,
        _operand_schema(keyword, operand(targets)),
        control=_operand_schema(keyword, targets.t),
    )


@pytest.mark.parametrize("keyword", KEYWORDS)
def test_invalid_pattern_operand_is_schema_error(
    gts_api, schema_dialect, keyword, subtests
):
    targets = _operand_targets(gts_api, schema_dialect)
    for case in INVALID_PATTERNS:
        (operand,) = case.values
        with case_subtest(subtests, case=case.id, operand=operand):
            api = GtsTestAPI(gts_api.session, gts_api.base_url)
            _assert_schema_error(
                api,
                schema_dialect,
                _operand_schema(keyword, operand),
                control=_operand_schema(keyword, targets.t),
            )


# Schema locations are traversed according to the dialect, including locations
# no value reaches; a schema error is not inverted by `not` or rescued by an
# `anyOf` branch (§9.6.3). The removed x-gts-ref and an unknown x-gts-* keyword
# follow the same lifecycle (§11.0).

def _defs_key(dialect):
    return "definitions" if "draft-07" in dialect else "$defs"


LOCATIONS = {
    "property": lambda ref, d: _holder(ref),
    "array_items": lambda ref, d: {
        "type": "object",
        "properties": {"refs": {"type": "array", "items": ref}},
    },
    "unused_definition": lambda ref, d: {"type": "object", _defs_key(d): {"Unused": ref}},
    "inactive_any_of": lambda ref, d: _holder({"anyOf": [{"type": "string"}, ref]}),
    "not": lambda ref, d: _holder({"not": ref}),
    "unselected_then": lambda ref, d: _holder({"if": {"type": "number"}, "then": ref}),
    "trait_schema": lambda ref, d: {
        "type": "object",
        "x-gts-traits-schema": {"type": "object", "properties": {"ref": ref}},
    },
}

LOCATION_CASES = (
    pytest.param(TYPE_REF, lambda r: r.it, TYPE_REF, id="type_ref_instance_operand"),
    pytest.param(INSTANCE_REF, lambda r: "/$id/", INSTANCE_REF, id="instance_ref_pointer"),
    pytest.param("x-gts-ref", lambda r: r.t, INSTANCE_REF, id="legacy_x_gts_ref"),
    pytest.param("x-gts-entity-ref", lambda r: r.t, INSTANCE_REF, id="unknown_keyword"),
)


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("keyword,operand,control_keyword", LOCATION_CASES)
def test_schema_error_at_every_schema_location(
    gts_api, schema_dialect, location, keyword, operand, control_keyword
):
    api = gts_api
    targets = _operand_targets(api, schema_dialect)
    build = LOCATIONS[location]
    _assert_schema_error(
        api,
        schema_dialect,
        build({"type": "string", keyword: operand(targets)}, schema_dialect),
        control=build({"type": "string", control_keyword: targets.t}, schema_dialect),
    )


REFERENCE_KEYS = (TYPE_REF, INSTANCE_REF, "x-gts-ref")


def test_literal_data_and_property_names_are_not_keywords(gts_api, schema_dialect):
    """Keyword-shaped keys inside literal data and property names are allowed.

    test_schema_error_at_every_schema_location shows that the same operands
    are schema errors at schema locations.
    """
    api = gts_api
    literal = {key: "not-a-gts-id" for key in REFERENCE_KEYS}
    schema = {
        "type": "object",
        "properties": {
            **{key: {"type": "string"} for key in REFERENCE_KEYS},
            "constData": {"const": literal},
            "enumData": {"enum": [literal, {key: 42 for key in REFERENCE_KEYS}]},
            "defaultData": {"type": "object", "default": literal},
            "exampleData": {"type": "object", "examples": [literal]},
        },
        "x-gts-traits-schema": {
            "type": "object",
            "properties": {"meta": {"type": "object", "default": literal}},
        },
    }
    holder = api.register("holder", schema, schema_dialect, mode="none")
    api.check_type_schema(holder, valid=True, mode="none")
    leaf = _register_type(
        api,
        schema_dialect,
        api.derived_type_id(holder, "leaf"),
        {
            "type": "object",
            "allOf": [{"$ref": "gts://" + holder}],
            "x-gts-traits": {"meta": literal},
        },
        mode="none",
    )
    api.check_type_schema(leaf, valid=True, mode="none")
    _check_payloads(
        api,
        holder,
        [({key: "not-a-gts-id" for key in REFERENCE_KEYS}, True)],
        mode="none",
    )


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_candidate_kind_and_matching(gts_api, schema_dialect, keyword, mode):
    """Registry lookup does not replace kind or matching.

    Every concrete candidate is registered and valid, so in every policy a
    rejection can come only from matching or kind (ADR-0008 candidate table).
    Detailed §10 matching is in the shared test cases below.
    """
    api = gts_api
    r = _targets(api, schema_dialect)
    holder = api.register(
        "holder", _holder({"type": "string", keyword: r.t}), schema_dialect, mode=mode
    )
    want_type = keyword == TYPE_REF
    # In M(r.t): the type, an explicit minor, a derived type, and instances.
    types_in = (r.t, r.tm, r.d)
    instances_in = (r.it, r.itm, r.idv, r.u)
    expectations = [(c, want_type) for c in types_in]
    expectations += [(c, not want_type) for c in instances_in]
    # Outside M(r.t): another major, another type, and its instance.
    expectations += [(c, False) for c in (r.t2, r.other, r.oi)]
    # Malformed candidates, including ones with a matching root and the
    # required final-character kind: a prefix and suffix check is not enough.
    malformed = [r.t + "*", "gts://" + r.t, "not-a-gts-id", ""]
    if want_type:
        malformed += [r.t + "x.pytest._.Bad.v1~", r.t + "x.pytest._.bad.v01~"]
    else:
        malformed += [
            r.t + "x.pytest._.Bad.v1",
            r.t + "x.pytest._.bad",
            r.t + UUID[:-1],
        ]
    expectations += [(c, False) for c in malformed]
    _check_refs(api, holder, expectations, mode)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("operand_tail", ["named", "uuid"])
def test_instance_operand_matching_under_lookup(
    gts_api, schema_dialect, operand_tail, mode
):
    """A registered, valid instance outside M(operand) is still rejected when
    lookup is enabled. Version and chain combinations are in the shared test cases."""
    api = gts_api
    t = _register_type(api, schema_dialect, api.type_id("target"))
    if operand_tail == "named":
        right = api.register_instance(t, {}, validate=True)
        # A textual extension of the operand across the major-version digits.
        wrong = _register_instance_id(api, t, right + "2")
    else:
        right = _register_uuid_instance(api, t)
        wrong = _register_instance_id(
            api, t, t + "7a1d2f34-5678-49ab-9012-abcdef123457"
        )
    api.check_instance(wrong, valid=True)
    holder = api.register(
        "holder",
        _holder({"type": "string", INSTANCE_REF: right}),
        schema_dialect,
        mode=mode,
    )
    _check_refs(api, holder, [(right, True), (wrong, False)], mode)


# ---------------------------------------------------------------------------
# Transient instances: explicit type and type inferred from the payload
# ---------------------------------------------------------------------------

def _check_transient_payload(api, type_id, payload, valid, type_selection):
    """Validate without registering the payload; targets are registered separately."""
    try:
        if type_selection == "explicit":
            api.check_payload(type_id, payload, valid=valid)
        else:
            result = api.request(
                "POST", "/validate-json", json={**payload, "type": type_id}
            )
            assert result["is_type_schema"] is False, result
            api.verdict(result, valid)
    except AssertionError as error:
        raise AssertionError(
            f"{type_selection} type {type_id}: payload {payload!r} "
            f"expected valid={valid}: {error}"
        ) from None


@pytest.mark.parametrize("type_selection", ["explicit", "inferred"])
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_transient_payload_checks_candidate_kind_and_matching(
    gts_api, schema_dialect, keyword, type_selection
):
    """Both transient endpoints enforce the keyword on instance field values.

    All concrete candidates are registered and valid, so kind and matching
    are tested independently of the endpoint's reference lookup policy.
    """
    api = gts_api
    r = _targets(api, schema_dialect)
    holder = api.register(
        "holder", _holder({"type": "string", keyword: r.t}), schema_dialect
    )
    want_type = keyword == TYPE_REF
    expectations = [(candidate, want_type) for candidate in (r.t, r.tm, r.d)]
    expectations += [
        (candidate, not want_type) for candidate in (r.it, r.itm, r.idv, r.u)
    ]
    expectations += [(candidate, False) for candidate in (r.t2, r.other, r.oi)]
    expectations += [(r.t + "*", False), ("not-a-gts-id", False)]
    for candidate, valid in expectations:
        _check_transient_payload(
            api, holder, {"ref": candidate}, valid, type_selection
        )
    _check_transient_payload(api, holder, {}, True, type_selection)


@pytest.mark.parametrize("type_selection", ["explicit", "inferred"])
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_transient_payload_self_reference_uses_selected_leaf(
    gts_api, schema_dialect, keyword, type_selection
):
    """Inherited `/$id` is rebound to the selected leaf on both transient paths."""
    api = gts_api
    base = _register_type(
        api,
        schema_dialect,
        api.type_id("base"),
        _holder({"type": "string", keyword: "/$id"}),
    )
    sibling = _register_derived(api, schema_dialect, base, "sibling")
    leaf = _register_derived(api, schema_dialect, base, "leaf")
    further = _register_derived(api, schema_dialect, leaf, "further")
    types = (base, sibling, leaf, further)
    instances = [api.register_instance(t, {}, validate=True) for t in types]
    want_type = keyword == TYPE_REF
    for selected, accepted_types in ((leaf, {leaf, further}), (further, {further})):
        for candidate_type, candidate_instance in zip(types, instances):
            in_scope = candidate_type in accepted_types
            _check_transient_payload(
                api, selected, {"ref": candidate_type}, in_scope and want_type,
                type_selection,
            )
            _check_transient_payload(
                api, selected, {"ref": candidate_instance}, in_scope and not want_type,
                type_selection,
            )


@pytest.mark.parametrize("type_selection", ["explicit", "inferred"])
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_transient_payload_rejects_deferred_invalid_operand(
    gts_api, schema_dialect, keyword, type_selection
):
    """Stored invalid operands fail even when the transient payload omits `ref`.

    Registration without validation may reject early. If it stores the
    schema, neither transient endpoint may treat that as proof of validity.
    """
    api = gts_api
    r = _operand_targets(api, schema_dialect)
    control = api.register(
        "control", _operand_schema(keyword, r.t), schema_dialect
    )
    candidate = r.t if keyword == TYPE_REF else r.it
    payloads = ({}, {"ref": candidate})
    for payload in payloads:
        _check_transient_payload(api, control, payload, True, type_selection)

    invalid_operand = r.it if keyword == TYPE_REF else "/$id/"
    deferred = api.register_deferred(
        "deferred", _operand_schema(keyword, invalid_operand), schema_dialect
    )
    if deferred is not None:
        for payload in payloads:
            _check_transient_payload(api, deferred, payload, False, type_selection)


# §10 matching test cases (shared_id_pattern_cases.py), shared with OP#4 and
# x-gts-pattern-ref. Lookup is disabled, so candidates are not registered: a
# verdict comes only from candidate syntax, kind and matching.

def _is_concrete_instance(pattern):
    return "*" not in pattern and not _is_type_id(pattern)


def _check_shared_case_ref(api, dialect, keyword, operand, candidate, valid, holders, index):
    if operand not in holders:
        holders[operand] = api.register(
            f"holder{index}",
            _holder({"type": "string", keyword: operand}),
            dialect,
            mode="none",
        )
    instance = api.register_instance(
        holders[operand], {"ref": candidate}, name=f"c{index}"
    )
    api.check_instance(instance, valid=valid, mode="none")


@pytest.mark.parametrize("keyword", KEYWORDS)
def test_shared_candidate(gts_api, schema_dialect, keyword, subtests):
    """A candidate is accepted iff it is in M(operand) and has the kind."""
    holders = {}
    for index, case in enumerate(MATCH_CASES):
        operand, candidate, expect = case.values
        # Concrete Instance ID operands are schema errors for type-ref, tested below.
        if keyword == TYPE_REF and _is_concrete_instance(operand):
            continue
        valid = expect.matches and _is_type_id(candidate) == (keyword == TYPE_REF)
        with case_subtest(
            subtests, case=case.id, operand=operand, candidate=candidate, expected=valid
        ):
            _check_shared_case_ref(
                gts_api,
                schema_dialect,
                keyword,
                operand,
                candidate,
                valid,
                holders,
                index,
            )


@pytest.mark.parametrize("keyword", KEYWORDS)
def test_shared_pattern_candidate_is_rejected(
    gts_api, schema_dialect, keyword, subtests
):
    """Coverage does not apply to entity references: a pattern candidate is
    rejected even when the operand covers it."""
    holders = {}
    for index, case in enumerate(COVERAGE_CASES):
        operand, candidate, covered, _ = case.values
        if not covered or (keyword == TYPE_REF and _is_concrete_instance(operand)):
            continue
        with case_subtest(
            subtests, case=case.id, operand=operand, candidate=candidate, expected=False
        ):
            _check_shared_case_ref(
                gts_api,
                schema_dialect,
                keyword,
                operand,
                candidate,
                False,
                holders,
                index,
            )


def test_shared_instance_operand_is_type_ref_error(gts_api, schema_dialect, subtests):
    """A concrete Instance ID operand is valid for x-gts-instance-ref and a
    schema error, not a value failure, for x-gts-type-ref. POST /validate-json
    is checked with registered targets in
    test_instance_operand_is_valid_only_for_instance_ref."""
    operands = sorted(
        {
            case.values[0]
            for case in (*MATCH_CASES, *COVERAGE_CASES)
            if _is_concrete_instance(case.values[0])
        }
    )
    for operand in operands:
        with case_subtest(subtests, case=operand, operand=operand):
            api = GtsTestAPI(gts_api.session, gts_api.base_url)
            control = api.register(
                "control",
                _holder({"type": "string", INSTANCE_REF: operand}),
                schema_dialect,
                mode="none",
            )
            api.check_type_schema(control, valid=True, mode="none")
            _assert_stored_schema_error(
                api, schema_dialect, _holder({"type": "string", TYPE_REF: operand})
            )


@pytest.mark.parametrize("keyword", KEYWORDS)
def test_keywords_constrain_strings_only(gts_api, schema_dialect, keyword):
    api = gts_api
    r = _targets(api, schema_dialect)
    untyped = api.register("untyped", _holder({keyword: r.t}), schema_dialect, mode="none")
    right, wrong = (r.d, r.it) if keyword == TYPE_REF else (r.it, r.d)
    _check_payloads(
        api,
        untyped,
        [
            ({}, True),
            ({"ref": 42}, True),
            ({"ref": None}, True),
            ({"ref": True}, True),
            ({"ref": {}}, True),
            ({"ref": [wrong]}, True),
            ({"ref": right}, True),
            # The keyword itself is active on strings.
            ({"ref": wrong}, False),
        ],
        mode="none",
    )
    typed = api.register(
        "typed", _holder({"type": "string", keyword: r.t}), schema_dialect, mode="none"
    )
    _check_payloads(api, typed, [({"ref": 42}, False), ({}, True)], mode="none")


COMPOSITIONS = {
    "any_of_union": (
        lambda r: {"anyOf": [{TYPE_REF: r.t}, {INSTANCE_REF: r.t}]},
        lambda r: {r.t, r.tm, r.d, r.it, r.u},
    ),
    "one_of_union": (
        lambda r: {"oneOf": [{TYPE_REF: r.t}, {INSTANCE_REF: r.t}]},
        lambda r: {r.t, r.tm, r.d, r.it, r.u},
    ),
    # Unsatisfiable, but not a schema error (ADR-0008).
    "same_object": (lambda r: {TYPE_REF: r.t, INSTANCE_REF: r.t}, lambda r: set()),
    "all_of": (
        lambda r: {"allOf": [{TYPE_REF: r.t}, {INSTANCE_REF: r.t}]},
        lambda r: set(),
    ),
    # Value failures, including malformed candidates, are invertible.
    "not_type_ref": (
        lambda r: {"not": {TYPE_REF: r.t}},
        lambda r: {r.it, r.u, r.other, r.oi, "not-a-gts-id"},
    ),
    "not_instance_ref": (
        lambda r: {"not": {INSTANCE_REF: r.t}},
        lambda r: {r.t, r.tm, r.d, r.other, r.oi, "not-a-gts-id"},
    ),
    "const_pins_type": (lambda r: {TYPE_REF: r.t, "const": r.t}, lambda r: {r.t}),
    "const_pins_instance": (
        lambda r: {INSTANCE_REF: r.t, "const": r.it},
        lambda r: {r.it},
    ),
}


@pytest.mark.parametrize("composition", COMPOSITIONS)
def test_composition(gts_api, schema_dialect, composition):
    api = gts_api
    r = _targets(api, schema_dialect)
    build, accepted = COMPOSITIONS[composition]
    holder = api.register(
        "holder", _holder({"type": "string", **build(r)}), schema_dialect, mode="none"
    )
    api.check_type_schema(holder, valid=True, mode="none")
    candidates = (r.t, r.tm, r.d, r.it, r.u, r.other, r.oi, "not-a-gts-id")
    _check_refs(api, holder, [(c, c in accepted(r)) for c in candidates])


# ---------------------------------------------------------------------------
# Selected-leaf `/$id`
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("form", ["inherited_ref", "inline_all_of"])
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_self_reference_resolves_to_selected_leaf(gts_api, schema_dialect, keyword, form):
    """`/$id` resolves to the selected leaf through `$ref` and inline `allOf`.

    inherited_ref: the base declares the constraint and descendants import it.
    inline_all_of: the leaf declares it inside its own `allOf`.
    """
    api = gts_api
    constraint = {
        "type": "object",
        "properties": {"ref": {"type": "string", keyword: "/$id"}},
    }
    base = _register_type(
        api,
        schema_dialect,
        api.type_id("base"),
        constraint if form == "inherited_ref" else None,
        mode="none",
    )
    sibling = _register_derived(api, schema_dialect, base, "sibling", mode="none")
    leaf_id = api.derived_type_id(base, "leaf")
    leaf_parts = [{"$ref": "gts://" + base}]
    if form == "inline_all_of":
        leaf_parts.append(constraint)
    leaf = _register_type(
        api,
        schema_dialect,
        leaf_id,
        {"type": "object", "allOf": leaf_parts},
        mode="none",
    )
    further = _register_derived(api, schema_dialect, leaf, "further", mode="none")

    def instance(type_id):
        return type_id + "x.pytest._.item.v1"

    def expect(selected_types, selected_instances):
        candidates = [base, sibling, leaf, further]
        candidates += [instance(c) for c in candidates]
        candidates += ["not-a-gts-id"]
        selected = selected_types if keyword == TYPE_REF else selected_instances
        return [(c, c in selected) for c in candidates]

    # Selected leaf: itself and its descendants; never ancestor or sibling.
    _check_refs(
        api,
        leaf,
        expect({leaf, further}, {instance(leaf), instance(further)}),
    )
    # Further derivation rebinds the root again.
    _check_refs(api, further, expect({further}, {instance(further)}))


@pytest.mark.parametrize("keyword", KEYWORDS)
def test_chained_id_does_not_import_self_reference(gts_api, schema_dialect, keyword):
    """A chained `$id` alone does not import the base's `/$id` constraint.

    The child re-declares the field with the literal base root, which keeps the
    base scope (a valid derivation). Only an implicitly imported, leaf-rooted
    `/$id` would reject an ancestor-rooted candidate.
    """
    api = gts_api
    base = _register_type(
        api,
        schema_dialect,
        api.type_id("base"),
        _holder({"type": "string", keyword: "/$id"}),
        mode="none",
    )
    base_instance = api.register_instance(base, {}, name="target", validate=True)
    child = _register_type(
        api,
        schema_dialect,
        api.derived_type_id(base, "child"),
        _holder({"type": "string", keyword: base}),
    )
    api.check_type_schema(child, valid=True)
    candidate = base if keyword == TYPE_REF else base_instance
    _check_refs(api, child, [(candidate, True)])


# ---------------------------------------------------------------------------
# Registry policies: operand lookup is independent of candidate kind
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_policy_checks_candidate_targets(gts_api, schema_dialect, keyword, mode):
    api = gts_api
    item = _register_type(
        api,
        schema_dialect,
        api.type_id("item"),
        {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
    )
    good = api.register_instance(item, {"name": "good"}, name="good", validate=True)
    bad = api.register_instance(item, {}, name="bad")
    api.check_instance(bad, valid=False)
    broken = _register_type(
        api,
        schema_dialect,
        api.type_id("broken"),
        {
            "type": "object",
            "x-gts-traits-schema": {
                "type": "object",
                "required": ["retention"],
                "properties": {"retention": {"type": "string"}},
            },
        },
        validate=False,
    )
    api.check_type_schema(broken, valid=False)
    holder = api.register(
        "holder",
        _holder({"type": "string", keyword: api.id_prefix + ".*"}),
        schema_dialect,
        mode=mode,
    )
    lookup = mode != "none"
    if keyword == TYPE_REF:
        valid, invalid, missing = item, broken, api.type_id("missing")
        wrong_kind = good
    else:
        valid, invalid, missing = good, bad, item + "x.pytest._.missing.v1"
        wrong_kind = item
    _check_refs(
        api,
        holder,
        [
            (valid, True),
            (invalid, mode != "any-valid"),
            (missing, not lookup),
            (wrong_kind, False),
        ],
        mode,
    )


@pytest.mark.parametrize("mode", ["any-present", "any-valid"])
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_wildcard_operand_witness_may_have_either_kind(
    gts_api, schema_dialect, keyword, mode
):
    """An entity of the other kind satisfies wildcard operand lookup, but does
    not make an unregistered candidate of the required kind present."""
    api = gts_api
    base = _register_type(api, schema_dialect, api.type_id("base"))
    holder = api.register(
        "holder",
        _holder({"type": "string", keyword: base + "x.pytest.*"}),
        schema_dialect,
        validate=False,
    )
    api.check_type_schema(holder, valid=False, mode=mode)

    if keyword == TYPE_REF:
        witness = api.register_instance(base, {}, name="witness", validate=True)
        candidate = api.derived_type_id(base, "candidate")
    else:
        witness = _register_derived(api, schema_dialect, base, "witness")
        candidate = base + "x.pytest._.candidate.v1"
    api.check_type_schema(holder, valid=True, mode=mode)
    _check_refs(api, holder, [(candidate, False), (witness, False)], mode)

    if keyword == TYPE_REF:
        _register_derived(api, schema_dialect, base, "candidate")
    else:
        api.register_instance(base, {}, name="candidate", validate=True)
    instance_id = api.register_instance(holder, {"ref": candidate}, name="after")
    api.check_instance(instance_id, valid=True, mode=mode)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("target", ["missing", "invalid"])
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_policy_checks_concrete_operand_target(
    gts_api, schema_dialect, keyword, target, mode
):
    api = gts_api
    if target == "missing":
        operand = api.type_id("missing")
        valid = mode == "none"
    else:
        operand = _register_type(
            api,
            schema_dialect,
            api.type_id("broken"),
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "required": ["retention"],
                    "properties": {"retention": {"type": "string"}},
                },
            },
            validate=False,
        )
        api.check_type_schema(operand, valid=False)
        valid = mode != "any-valid"
    holder = api.register(
        "holder",
        _holder({"type": "string", keyword: operand}),
        schema_dialect,
        validate=False,
    )
    api.check_type_schema(holder, valid=valid, mode=mode)


@pytest.mark.parametrize("mode", ["any-present", "any-valid"])
def test_abstract_and_final_targets(gts_api, schema_dialect, mode):
    """Abstract and final types are permitted operands and type targets; target
    validity still applies derivation and instantiation rules."""
    api = gts_api
    abstract = _register_type(
        api, schema_dialect, api.type_id("abstract"), {"type": "object", "x-gts-abstract": True}
    )
    concrete = _register_derived(api, schema_dialect, abstract, "concrete")
    concrete_instance = api.register_instance(concrete, {}, validate=True)
    abstract_instance = api.register_instance(abstract, {}, name="illegal")
    api.check_instance(abstract_instance, valid=False)
    final = _register_type(
        api, schema_dialect, api.type_id("final"), {"type": "object", "x-gts-final": True}
    )
    final_instance = api.register_instance(final, {}, validate=True)
    final_derived = _register_derived(api, schema_dialect, final, "illegal", validate=False)
    api.check_type_schema(final_derived, valid=False)

    holder = api.register(
        "holder",
        {
            "type": "object",
            "properties": {
                "abstractType": {"type": "string", TYPE_REF: abstract},
                "abstractInstance": {"type": "string", INSTANCE_REF: abstract},
                "finalType": {"type": "string", TYPE_REF: final},
                "finalInstance": {"type": "string", INSTANCE_REF: final},
            },
        },
        schema_dialect,
        mode=mode,
    )
    lenient = mode == "any-present"
    _check_payloads(
        api,
        holder,
        [
            ({"abstractType": abstract}, True),
            ({"abstractType": concrete}, True),
            ({"abstractInstance": concrete_instance}, True),
            ({"abstractInstance": abstract_instance}, lenient),
            ({"finalType": final}, True),
            ({"finalType": final_derived}, lenient),
            ({"finalInstance": final_instance}, True),
        ],
        mode,
    )


# ---------------------------------------------------------------------------
# Traits
# ---------------------------------------------------------------------------

TRAIT_CASES = (
    # leaf traits, intermediate traits, default of `i`, abstract leaf, valid
    pytest.param({"t": "d", "i": "it"}, None, None, False, True, id="leaf_values"),
    pytest.param({"i": "u"}, None, None, False, True, id="leaf_uuid_instance"),
    pytest.param({"t": "it"}, None, None, False, False, id="type_trait_gets_instance"),
    pytest.param({"i": "d"}, None, None, False, False, id="instance_trait_gets_type"),
    pytest.param({"t": "d"}, {"i": "it"}, None, False, True, id="inherited"),
    pytest.param({"t": "d"}, {"i": "d"}, None, False, False, id="inherited_wrong_kind"),
    pytest.param({"t": "d"}, None, "it", False, True, id="default"),
    pytest.param({"t": "d"}, None, "d", False, False, id="default_wrong_kind"),
    pytest.param({"t": "d"}, None, None, True, True, id="abstract"),
    pytest.param({"t": "it"}, None, None, True, False, id="abstract_wrong_kind"),
)


@pytest.mark.parametrize("mode", ["none", "any-valid"])
@pytest.mark.parametrize("leaf_traits,middle_traits,default,abstract,valid", TRAIT_CASES)
def test_trait_values(
    gts_api, schema_dialect, mode, leaf_traits, middle_traits, default, abstract, valid
):
    """Leaf, inherited, default, and abstract-type trait values are checked
    for kind; all targets are registered and valid."""
    api = gts_api
    r = _targets(api, schema_dialect)
    instance_trait = {"type": "string", INSTANCE_REF: r.t}
    if default:
        instance_trait["default"] = getattr(r, default)
    base = _register_type(
        api,
        schema_dialect,
        api.type_id("base"),
        {
            "type": "object",
            "x-gts-abstract": True,
            "x-gts-traits-schema": {
                "type": "object",
                "properties": {
                    "t": {"type": "string", TYPE_REF: r.t},
                    "i": instance_trait,
                },
            },
        },
        validate=False,
    )
    parent = base
    if middle_traits:
        parent = _register_type(
            api,
            schema_dialect,
            api.derived_type_id(base, "middle"),
            {
                "type": "object",
                "allOf": [{"$ref": "gts://" + base}],
                "x-gts-abstract": True,
                "x-gts-traits": {k: getattr(r, v) for k, v in middle_traits.items()},
            },
            validate=False,
        )
    leaf_schema = {
        "type": "object",
        "allOf": [{"$ref": "gts://" + parent}],
        "x-gts-traits": {k: getattr(r, v) for k, v in leaf_traits.items()},
    }
    if abstract:
        leaf_schema["x-gts-abstract"] = True
    leaf = _register_type(
        api, schema_dialect, api.derived_type_id(parent, "leaf"), leaf_schema, validate=False
    )
    api.check_type_schema(leaf, valid=valid, mode=mode)


@pytest.mark.parametrize(
    "selected,valid",
    [
        ("leaf", True),
        ("descendant", True),
        ("middle", False),
        ("base", False),
        ("leaf_wrong_kind", False),
    ],
)
@pytest.mark.parametrize("keyword", KEYWORDS)
def test_trait_self_reference(gts_api, schema_dialect, keyword, selected, valid):
    """`/$id` in a trait schema resolves to the leaf being validated, not to
    the type that declares the trait schema."""
    api = gts_api
    base = api.type_id("base")
    middle = api.derived_type_id(base, "middle")
    leaf = api.derived_type_id(middle, "leaf")
    root = {
        "leaf": leaf,
        "descendant": api.derived_type_id(leaf, "child"),
        "middle": middle,
        "base": base,
        "leaf_wrong_kind": leaf,
    }[selected]
    as_instance = (keyword == INSTANCE_REF) != (selected == "leaf_wrong_kind")
    value = root + "x.pytest._.item.v1" if as_instance else root
    _register_type(
        api,
        schema_dialect,
        base,
        {
            "type": "object",
            "x-gts-abstract": True,
            "x-gts-traits-schema": {
                "type": "object",
                "properties": {"self": {"type": "string", keyword: "/$id"}},
            },
        },
        mode="none",
    )
    _register_type(
        api,
        schema_dialect,
        middle,
        {"type": "object", "allOf": [{"$ref": "gts://" + base}], "x-gts-abstract": True},
        mode="none",
    )
    _register_type(
        api,
        schema_dialect,
        leaf,
        {
            "type": "object",
            "allOf": [{"$ref": "gts://" + middle}],
            "x-gts-traits": {"self": value},
        },
        validate=False,
    )
    api.check_type_schema(leaf, valid=valid, mode="none")
