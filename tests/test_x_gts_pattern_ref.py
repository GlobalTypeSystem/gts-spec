"""x-gts-pattern-ref conformance tests (README §9.6.2, §10; ADR-0007).

Each test registers a schema whose `scope` property carries the keyword and
validates payloads against it. Syntax and coverage vectors come from the
shared test cases in shared_id_pattern_cases.py: a value is valid iff
M(value) ⊆ M(operand), and every uncovered row names a witness.
"""

import pytest

from .helpers.shared_cases import case_subtest
from .helpers.http_client import GtsTestAPI
from .shared_id_pattern_cases import (
    BUCKET,
    BUCKET_FAMILY,
    COVERAGE_CASES,
    FAMILY,
    INSTANCE,
    INVALID_PATTERNS,
    MATCH_CASES,
    OTHER,
    RESOURCE,
    VALID_PATTERNS,
)


def _scope_schema(scope):
    return {
        "type": "object",
        "required": ["scope"],
        "properties": {"scope": scope},
    }


def _register_scope(api, dialect, operand, name="scope"):
    return api.register(
        name,
        _scope_schema({"type": "string", "x-gts-pattern-ref": operand}),
        dialect,
    )


# ---------------------------------------------------------------------------
# Syntax: `gts.*` accepts every well-formed pattern and nothing else.
# ---------------------------------------------------------------------------


def test_universal_operand_accepts_valid_pattern(gts_api, schema_dialect, subtests):
    api = gts_api
    scope_type = _register_scope(api, schema_dialect, "gts.*")
    for case in VALID_PATTERNS:
        (value,) = case.values
        with case_subtest(subtests, case=case.id, value=value, expected=True):
            api.check_payload(scope_type, {"scope": value}, valid=True)


def test_universal_operand_rejects_invalid_pattern(gts_api, schema_dialect, subtests):
    api = gts_api
    scope_type = _register_scope(api, schema_dialect, "gts.*")
    for case in INVALID_PATTERNS:
        (value,) = case.values
        with case_subtest(subtests, case=case.id, value=value, expected=False):
            api.check_payload(scope_type, {"scope": value}, valid=False)


# ---------------------------------------------------------------------------
# Coverage: a value is valid when the operand selects everything it selects.
# ---------------------------------------------------------------------------


def _check_coverage(api, dialect, operand, value, covered, witness, scopes, index):
    def registered_scope(pattern, role):
        if pattern not in scopes:
            scopes[pattern] = _register_scope(
                api, dialect, pattern, name=f"{role}{index}"
            )
        return scopes[pattern]

    scope_type = registered_scope(operand, "scope")
    api.check_payload(scope_type, {"scope": value}, valid=covered)
    if not covered:
        # The witness proves the verdict: the value's own scope accepts it,
        # and the operand's scope rejects it.
        value_scope_type = registered_scope(value, "value_scope")
        api.check_payload(value_scope_type, {"scope": witness}, valid=True)
        if witness != value:
            api.check_payload(scope_type, {"scope": witness}, valid=False)


def test_concrete_value_coverage(gts_api, schema_dialect, subtests):
    """A concrete value selects itself and, under omitted minors or a type
    chain, more identifiers; an uncovered value is its own witness."""
    scopes = {}
    for index, case in enumerate(MATCH_CASES):
        operand, value, expect = case.values
        with case_subtest(
            subtests,
            case=case.id,
            operand=operand,
            value=value,
            expected=expect.covered,
        ):
            _check_coverage(
                gts_api,
                schema_dialect,
                operand,
                value,
                expect.covered,
                value,
                scopes,
                index,
            )


def test_wildcard_value_coverage(gts_api, schema_dialect, subtests):
    scopes = {}
    for index, case in enumerate(COVERAGE_CASES):
        operand, value, covered, witness = case.values
        with case_subtest(
            subtests,
            case=case.id,
            operand=operand,
            value=value,
            expected=covered,
            witness=witness,
        ):
            _check_coverage(
                gts_api, schema_dialect, operand, value, covered, witness, scopes, index
            )


@pytest.mark.parametrize(
    "operand,value,valid",
    [
        pytest.param(FAMILY, RESOURCE, True, id="covered_concrete"),
        pytest.param(RESOURCE, BUCKET_FAMILY, True, id="covered_wildcard"),
        pytest.param(RESOURCE, FAMILY, False, id="uncovered"),
        pytest.param("gts.*", "gts.vendor*", False, id="malformed"),
    ],
)
def test_not_inverts_value_verdict(gts_api, schema_dialect, operand, value, valid):
    """Uncovered and malformed values are ordinary validation failures, so
    `not` inverts them like any other verdict."""
    api = gts_api
    scope_type = _register_scope(api, schema_dialect, operand)
    negated_scope_type = api.register(
        "negated_scope",
        _scope_schema(
            {"type": "string", "not": {"type": "string", "x-gts-pattern-ref": operand}}
        ),
        schema_dialect,
    )
    api.check_payload(scope_type, {"scope": value}, valid=valid)
    api.check_payload(negated_scope_type, {"scope": value}, valid=not valid)


# ---------------------------------------------------------------------------
# Applicability: the keyword constrains strings only.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(42, id="integer"),
        pytest.param(1.5, id="number"),
        pytest.param(True, id="boolean"),
        pytest.param(None, id="null"),
        pytest.param([], id="array"),
        pytest.param({}, id="object"),
    ],
)
def test_keyword_ignores_non_string_values(gts_api, schema_dialect, value):
    """Like `pattern`, the keyword accepts non-strings; `type` rejects them."""
    api = gts_api
    untyped_scope_type = api.register(
        "untyped_scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"x-gts-pattern-ref": FAMILY}},
        },
        schema_dialect,
    )
    string_scope_type = api.register(
        "string_scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": FAMILY}},
        },
        schema_dialect,
    )
    api.check_payload(untyped_scope_type, {"scope": value}, valid=True)
    api.check_payload(string_scope_type, {"scope": value}, valid=False)


def test_absent_optional_property_is_valid(gts_api, schema_dialect):
    """The keyword constrains a value only when one is present."""
    api = gts_api
    optional_scope_type = api.register(
        "optional_scope",
        {
            "type": "object",
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": FAMILY}},
        },
        schema_dialect,
    )
    api.check_payload(optional_scope_type, {}, valid=True)


# ---------------------------------------------------------------------------
# Invalid operands are schema errors, wherever they appear.
# ---------------------------------------------------------------------------


def assert_schema_error_everywhere(api, schema, dialect, payloads):
    """An invalid operand makes the schema invalid on every path (§9.6.2):

    1. registration with validation fails;
    2. POST /validate-json of the schema itself fails;
    3. if registration without validation stored the schema, validating the
       stored type fails, and so does every payload validated against it.
    """
    api.register("rejected", schema, dialect, status=422)
    api.check_transient_schema("transient", schema, dialect, valid=False)
    deferred_type = api.register_deferred("deferred", schema, dialect)
    if deferred_type is not None:
        api.check_type_schema(deferred_type, valid=False)
        for payload in payloads:
            api.check_payload(deferred_type, payload, valid=False)


# Invalid pattern strings from the shared test cases, plus non-strings and
# pointers other than `/$id`.
INVALID_OPERANDS = (
    *INVALID_PATTERNS,
    pytest.param(None, id="null"),
    pytest.param(True, id="boolean"),
    pytest.param(3, id="number"),
    pytest.param([], id="array"),
    pytest.param({}, id="object"),
    pytest.param("/", id="root_pointer"),
    pytest.param("/$schema", id="schema_pointer"),
    pytest.param("/properties/value", id="property_pointer"),
    pytest.param("/$id/", id="extended_self_pointer"),
)


def test_invalid_operand_is_not_inverted(gts_api, schema_dialect, subtests):
    """`not` around an invalid operand is still a schema error, never a match."""
    for case in INVALID_OPERANDS:
        (operand,) = case.values
        with case_subtest(subtests, case=case.id, operand=operand):
            # Preserve a separate registry namespace for each schema-error lifecycle.
            api = GtsTestAPI(gts_api.session, gts_api.base_url)
            assert_schema_error_everywhere(
                api,
                {
                    "type": "object",
                    "required": ["scope"],
                    "properties": {"scope": {"not": {"x-gts-pattern-ref": operand}}},
                },
                schema_dialect,
                payloads=[{"scope": RESOURCE}],
            )


def test_invalid_operand_on_optional_property_is_rejected(gts_api, schema_dialect):
    """The operand is invalid even when no payload supplies the property."""
    assert_schema_error_everywhere(
        gts_api,
        {
            "type": "object",
            "properties": {"scope": {"x-gts-pattern-ref": "/unsupported"}},
        },
        schema_dialect,
        # Operands are checked before any value is (§9.6.2): every payload
        # fails, whether it omits `scope`, holds a non-string, or a covered ID.
        payloads=[{}, {"scope": 42}, {"scope": RESOURCE}],
    )


def test_invalid_operand_in_unused_definition_is_rejected(gts_api, schema_dialect):
    """The operand is invalid even when no `$ref` reaches the definition."""
    definitions = "definitions" if "draft-07" in schema_dialect else "$defs"
    assert_schema_error_everywhere(
        gts_api,
        {
            "type": "object",
            definitions: {"Bad": {"x-gts-pattern-ref": "/unsupported"}},
        },
        schema_dialect,
        # Operands are checked before any value is (§9.6.2): every payload
        # fails, whether it omits `scope`, holds a non-string, or a covered ID.
        payloads=[{}, {"scope": 42}, {"scope": RESOURCE}],
    )


def test_invalid_operand_in_inactive_branch_is_rejected(gts_api, schema_dialect):
    """The operand is invalid even when `anyOf` succeeds through `true`."""
    assert_schema_error_everywhere(
        gts_api,
        {
            "type": "object",
            "anyOf": [True, {"x-gts-pattern-ref": "/unsupported"}],
        },
        schema_dialect,
        # Operands are checked before any value is (§9.6.2): every payload
        # fails, whether it omits `scope`, holds a non-string, or a covered ID.
        payloads=[{}, {"scope": 42}, {"scope": RESOURCE}],
    )


# ---------------------------------------------------------------------------
# Schema locations: the keyword applies wherever a subschema validates a value.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "holder_schema",
    [
        pytest.param(
            {
                "type": "object",
                "required": ["scope"],
                "properties": {
                    "scope": {"type": "string", "x-gts-pattern-ref": FAMILY},
                },
            },
            id="direct",
        ),
        pytest.param(
            {
                "type": "object",
                "required": ["scope"],
                "properties": {
                    "scope": {
                        "allOf": [
                            {"type": "string", "x-gts-pattern-ref": FAMILY},
                            {"type": "string", "x-gts-pattern-ref": RESOURCE},
                        ],
                    },
                },
            },
            id="allof",
        ),
        pytest.param(
            {
                "type": "object",
                "patternProperties": {
                    "^scope$": {"type": "string", "x-gts-pattern-ref": FAMILY},
                },
            },
            id="pattern_properties",
        ),
        pytest.param(
            {
                "type": "object",
                "additionalProperties": {
                    "type": "string",
                    "x-gts-pattern-ref": FAMILY,
                },
            },
            id="additional_properties",
        ),
    ],
)
def test_schema_locations(gts_api, schema_dialect, holder_schema):
    """RESOURCE is inside every scope below; `gts.*` is inside none."""
    api = gts_api
    holder = api.register("holder", holder_schema, schema_dialect)
    api.check_payload(holder, {"scope": RESOURCE}, valid=True)
    api.check_payload(holder, {"scope": "gts.*"}, valid=False)


def test_schema_location_anyof(gts_api, schema_dialect):
    """Inside `anyOf`, the scope branch rejects `gts.*` and `null` takes the
    other branch."""
    api = gts_api
    holder = api.register(
        "holder",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "anyOf": [
                        {"type": "string", "x-gts-pattern-ref": FAMILY},
                        {"type": "null"},
                    ],
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(holder, {"scope": RESOURCE}, valid=True)
    api.check_payload(holder, {"scope": "gts.*"}, valid=False)
    api.check_payload(holder, {"scope": None}, valid=True)


def test_schema_location_local_ref(gts_api, schema_dialect):
    """The keyword applies through a local `$ref` to a definition."""
    api = gts_api
    definitions = "definitions" if "draft-07" in schema_dialect else "$defs"
    holder = api.register(
        "holder",
        {
            "type": "object",
            "required": ["scope"],
            definitions: {
                "Selector": {"type": "string", "x-gts-pattern-ref": FAMILY},
            },
            "properties": {"scope": {"$ref": f"#/{definitions}/Selector"}},
        },
        schema_dialect,
    )
    api.check_payload(holder, {"scope": RESOURCE}, valid=True)
    api.check_payload(holder, {"scope": "gts.*"}, valid=False)


def test_array_items(gts_api, schema_dialect):
    """Every array item must be covered; an empty array has none to check."""
    api = gts_api
    scopes_type = api.register(
        "scopes",
        {
            "type": "object",
            "required": ["scopes"],
            "properties": {
                "scopes": {
                    "type": "array",
                    "items": {"type": "string", "x-gts-pattern-ref": FAMILY},
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(scopes_type, {"scopes": []}, valid=True)
    api.check_payload(scopes_type, {"scopes": [RESOURCE, BUCKET_FAMILY]}, valid=True)
    api.check_payload(scopes_type, {"scopes": [RESOURCE, "gts.*"]}, valid=False)


def test_positional_array_items(gts_api, schema_dialect):
    """The first item is scoped to FAMILY, later items to BUCKET."""
    api = gts_api
    if "2020-12" in schema_dialect:
        positional = {
            "type": "array",
            "prefixItems": [{"type": "string", "x-gts-pattern-ref": FAMILY}],
            "items": {"type": "string", "x-gts-pattern-ref": BUCKET},
        }
    else:
        positional = {
            "type": "array",
            "items": [{"type": "string", "x-gts-pattern-ref": FAMILY}],
            "additionalItems": {"type": "string", "x-gts-pattern-ref": BUCKET},
        }
    holder = api.register(
        "positional",
        {
            "type": "object",
            "required": ["scopes"],
            "properties": {"scopes": positional},
        },
        schema_dialect,
    )
    api.check_payload(holder, {"scopes": [RESOURCE, INSTANCE]}, valid=True)
    # RESOURCE is not inside BUCKET.
    api.check_payload(holder, {"scopes": [RESOURCE, RESOURCE]}, valid=False)
    api.check_payload(holder, {"scopes": ["gts.*"]}, valid=False)


def test_literal_data_and_property_named_keyword(gts_api, schema_dialect):
    """Only schema positions hold operands: the keyword inside `const`, `enum`,
    `default` or `examples` data, and a property named after the keyword, are
    ordinary data."""
    api = gts_api
    literal = {"x-gts-pattern-ref": "/invalid_in_data"}
    holder = api.register(
        "literal",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {"type": "string", "x-gts-pattern-ref": FAMILY},
                "x-gts-pattern-ref": {"type": "string"},
                "literal": {
                    "const": literal,
                    "enum": [literal],
                    "default": literal,
                    "examples": [literal],
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(
        holder,
        {"scope": RESOURCE, "x-gts-pattern-ref": "ordinary data", "literal": literal},
        valid=True,
    )
    api.check_payload(holder, {"scope": "gts.*"}, valid=False)


# ---------------------------------------------------------------------------
# `/$id`: the operand names the effective leaf schema being validated.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("selector_location", ["direct", "referenced_subschema"])
def test_self_reference_selects_effective_leaf(
    gts_api, schema_dialect, selector_location
):
    """`/$id` in an inherited property resolves to the leaf, not to the base
    that declares it, nor to an embedded resource's own `$id`."""
    api = gts_api
    base = api.type_id("base")
    middle = api.derived_type_id(base, "middle")
    leaf = api.derived_type_id(middle, "leaf")
    decoy = api.type_id("decoy")
    if selector_location == "direct":
        base_schema = {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": "/$id"}},
        }
    else:
        definitions = "definitions" if "draft-07" in schema_dialect else "$defs"
        base_schema = {
            "type": "object",
            "required": ["scope"],
            definitions: {
                # An embedded resource declares the hierarchy's dialect (README §11.0).
                "Selector": {
                    "$id": "gts://" + decoy,
                    "$schema": schema_dialect,
                    "type": "string",
                    "x-gts-pattern-ref": "/$id",
                },
            },
            "properties": {"scope": {"$ref": f"#/{definitions}/Selector"}},
        }
    api.register("base", base_schema, schema_dialect, type_id=base)
    api.register(
        "middle",
        {"allOf": [{"$ref": "gts://" + base}]},
        schema_dialect,
        type_id=middle,
    )
    api.register(
        "leaf", {"allOf": [{"$ref": "gts://" + middle}]}, schema_dialect, type_id=leaf
    )
    api.check_type_schema(leaf, valid=True)
    for inside_leaf in (
        leaf,
        leaf + "*",
        leaf + "acme.app._.child.v1~",
        leaf + "acme.app._.item.v1",
    ):
        api.check_payload(leaf, {"scope": inside_leaf}, valid=True)
    for outside_leaf in (
        base,
        middle,
        api.derived_type_id(middle, "sibling"),
        decoy,
        "gts.*",
    ):
        api.check_payload(leaf, {"scope": outside_leaf}, valid=False)


def test_self_reference_in_oneof(gts_api, schema_dialect):
    """Each `oneOf` branch resolves its own operand; FAMILY matches neither."""
    api = gts_api
    holder = api.register(
        "holder",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "oneOf": [
                        {"type": "string", "x-gts-pattern-ref": "/$id"},
                        {"type": "string", "x-gts-pattern-ref": OTHER},
                    ],
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(holder, {"scope": OTHER}, valid=True)
    api.check_payload(holder, {"scope": holder}, valid=True)
    api.check_payload(holder, {"scope": FAMILY}, valid=False)


# ---------------------------------------------------------------------------
# Traits: values are checked against `x-gts-traits-schema` after they are
# materialized for the effective leaf. Values given on the leaf, values
# inherited from an ancestor, and `default` values all have to be covered.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "trait_values,expected_validity",
    [
        pytest.param(
            [case.values[0] for case in VALID_PATTERNS], True, id="valid_shared_cases"
        ),
        pytest.param(
            [*(case.values[0] for case in VALID_PATTERNS), "gts.vendor*"],
            False,
            id="partial_token",
        ),
        pytest.param(["gts.*", "gts://" + RESOURCE], False, id="uri"),
        pytest.param([FAMILY + " "], False, id="whitespace"),
    ],
)
def test_trait_shared_syntax_cases(gts_api, schema_dialect, trait_values, expected_validity):
    """Under `gts.*`, a trait array is valid only if every item is a well-formed
    pattern."""
    api = gts_api
    holder = api.register(
        "holder",
        {
            "type": "object",
            "x-gts-traits-schema": {
                "type": "object",
                "properties": {
                    "scopes": {
                        "type": "array",
                        "items": {"type": "string", "x-gts-pattern-ref": "gts.*"},
                    },
                },
            },
            "x-gts-traits": {"scopes": trait_values},
        },
        schema_dialect,
        validate=False,
    )
    api.check_type_schema(holder, valid=expected_validity)


# FAMILY covers RESOURCE and BUCKET_FAMILY; it does not cover `gts.*`.
SCOPE_TRAIT_VALUES = [
    pytest.param([RESOURCE, BUCKET_FAMILY], True, id="covered"),
    pytest.param(["gts.*"], False, id="uncovered"),
]


@pytest.mark.parametrize("trait_values,expected_validity", SCOPE_TRAIT_VALUES)
def test_explicit_trait_values_on_leaf(
    gts_api, schema_dialect, trait_values, expected_validity
):
    """Values a concrete leaf gives in `x-gts-traits` must be covered by the
    trait schema's operand."""
    api = gts_api
    base = api.register(
        "base",
        {
            "type": "object",
            "x-gts-abstract": True,
            "x-gts-traits-schema": {
                "type": "object",
                "required": ["scopes"],
                "properties": {
                    "scopes": {
                        "type": "array",
                        "items": {"type": "string", "x-gts-pattern-ref": FAMILY},
                    },
                },
            },
        },
        schema_dialect,
        validate=False,
    )
    # The abstract base supplies no values, so it has nothing to check.
    api.check_type_schema(base, valid=True)

    leaf = api.derived_type_id(base, "leaf")
    leaf_schema = {
        "type": "object",
        "allOf": [{"$ref": "gts://" + base}],
        "x-gts-abstract": False,
        "x-gts-traits": {"scopes": trait_values},
    }
    if not expected_validity:
        # Registration with validation enforces trait values (§9.3).
        api.register("leaf", leaf_schema, schema_dialect, type_id=leaf, status=422)
    api.register("leaf", leaf_schema, schema_dialect, type_id=leaf, validate=False)
    api.check_type_schema(leaf, valid=expected_validity)


@pytest.mark.parametrize("trait_values,expected_validity", SCOPE_TRAIT_VALUES)
def test_inherited_trait_values(
    gts_api, schema_dialect, trait_values, expected_validity
):
    """Values the abstract base gives in `x-gts-traits` are checked on the base
    and again on the leaf that inherits them."""
    api = gts_api
    base_schema = {
        "type": "object",
        "x-gts-abstract": True,
        "x-gts-traits-schema": {
            "type": "object",
            "required": ["scopes"],
            "properties": {
                "scopes": {
                    "type": "array",
                    "items": {"type": "string", "x-gts-pattern-ref": FAMILY},
                },
            },
        },
        "x-gts-traits": {"scopes": trait_values},
    }
    if not expected_validity:
        # Registration with validation enforces trait values (§9.3).
        api.register("base", base_schema, schema_dialect, status=422)
    base = api.register("base", base_schema, schema_dialect, validate=False)
    api.check_type_schema(base, valid=expected_validity)

    leaf = api.derived_type_id(base, "leaf")
    leaf_schema = {
        "type": "object",
        "allOf": [{"$ref": "gts://" + base}],
        "x-gts-abstract": False,
    }
    if not expected_validity:
        api.register("leaf", leaf_schema, schema_dialect, type_id=leaf, status=422)
    api.register("leaf", leaf_schema, schema_dialect, type_id=leaf, validate=False)
    api.check_type_schema(leaf, valid=expected_validity)


@pytest.mark.parametrize("trait_values,expected_validity", SCOPE_TRAIT_VALUES)
def test_default_trait_values(gts_api, schema_dialect, trait_values, expected_validity):
    """A `default` in the trait schema is a supplied value: it is checked on
    the base and on the leaf that receives it."""
    api = gts_api
    base_schema = {
        "type": "object",
        "x-gts-abstract": True,
        "x-gts-traits-schema": {
            "type": "object",
            "required": ["scopes"],
            "properties": {
                "scopes": {
                    "type": "array",
                    "items": {"type": "string", "x-gts-pattern-ref": FAMILY},
                    "default": trait_values,
                },
            },
        },
    }
    if not expected_validity:
        # Registration with validation enforces trait values (§9.3).
        api.register("base", base_schema, schema_dialect, status=422)
    base = api.register("base", base_schema, schema_dialect, validate=False)
    api.check_type_schema(base, valid=expected_validity)

    leaf = api.derived_type_id(base, "leaf")
    leaf_schema = {
        "type": "object",
        "allOf": [{"$ref": "gts://" + base}],
        "x-gts-abstract": False,
    }
    if not expected_validity:
        api.register("leaf", leaf_schema, schema_dialect, type_id=leaf, status=422)
    api.register("leaf", leaf_schema, schema_dialect, type_id=leaf, validate=False)
    api.check_type_schema(leaf, valid=expected_validity)


@pytest.mark.parametrize(
    "trait_values,expected_validity",
    [
        *SCOPE_TRAIT_VALUES,
        pytest.param(["gts.vendor*"], False, id="malformed"),
    ],
)
def test_trait_values_supplied_on_abstract_type(
    gts_api, schema_dialect, trait_values, expected_validity
):
    """An abstract type need not supply traits, but the values it does supply
    are checked."""
    api = gts_api
    base = api.register(
        "base",
        {
            "type": "object",
            "x-gts-abstract": True,
            "x-gts-traits-schema": {
                "type": "object",
                "required": ["scopes"],
                "properties": {
                    "scopes": {
                        "type": "array",
                        "items": {"type": "string", "x-gts-pattern-ref": FAMILY},
                    },
                },
            },
        },
        schema_dialect,
        validate=False,
    )
    api.check_type_schema(base, valid=True)

    abstract_leaf = api.derived_type_id(base, "leaf")
    abstract_leaf_schema = {
        "type": "object",
        "allOf": [{"$ref": "gts://" + base}],
        "x-gts-abstract": True,
        "x-gts-traits": {"scopes": trait_values},
    }
    if not expected_validity:
        # Registration with validation enforces trait values (§9.3).
        api.register(
            "leaf",
            abstract_leaf_schema,
            schema_dialect,
            type_id=abstract_leaf,
            status=422,
        )
    api.register(
        "leaf",
        abstract_leaf_schema,
        schema_dialect,
        type_id=abstract_leaf,
        validate=False,
    )
    api.check_type_schema(abstract_leaf, valid=expected_validity)


@pytest.mark.parametrize(
    "selected,expected_validity",
    [
        pytest.param("leaf", True, id="leaf"),
        pytest.param("descendant", True, id="descendant"),
        pytest.param("ancestor", False, id="ancestor"),
        pytest.param("sibling", False, id="sibling"),
    ],
)
def test_inherited_trait_self_reference(
    gts_api, schema_dialect, selected, expected_validity
):
    """`/$id` in a trait schema resolves to the leaf being validated, not to
    the middle type that supplied the inherited value."""
    api = gts_api
    base = api.type_id("base")
    middle = api.derived_type_id(base, "middle")
    leaf = api.derived_type_id(middle, "leaf")
    selector_value = {
        "leaf": leaf,
        "descendant": leaf + "acme.app._.child.v1~",
        "ancestor": middle,
        "sibling": api.derived_type_id(middle, "other"),
    }[selected]
    api.register(
        "base",
        {
            "type": "object",
            "x-gts-abstract": True,
            "x-gts-traits-schema": {
                "type": "object",
                "required": ["selector"],
                "properties": {
                    "selector": {"type": "string", "x-gts-pattern-ref": "/$id"},
                },
            },
        },
        schema_dialect,
        type_id=base,
    )
    api.register(
        "middle",
        {
            "type": "object",
            "allOf": [{"$ref": "gts://" + base}],
            "x-gts-abstract": True,
            "x-gts-traits": {"selector": selector_value},
        },
        schema_dialect,
        type_id=middle,
    )
    # Every value above lies inside the middle type's own `/$id` scope.
    api.check_type_schema(middle, valid=True)
    api.register(
        "leaf",
        {"type": "object", "allOf": [{"$ref": "gts://" + middle}]},
        schema_dialect,
        type_id=leaf,
        validate=False,
    )
    api.check_type_schema(leaf, valid=expected_validity)


@pytest.mark.parametrize(
    "leaf_overrides_default,expected_validity",
    [
        pytest.param(False, False, id="leaf_inherits_default_base_id"),
        pytest.param(True, True, id="leaf_overrides_with_own_id"),
    ],
)
def test_trait_self_reference_after_default_materialization(
    gts_api, schema_dialect, leaf_overrides_default, expected_validity
):
    """A `default` naming the base is checked against the leaf's `/$id`, which
    the base is not inside; the leaf can override it with its own ID."""
    api = gts_api
    base = api.type_id("base")
    leaf = api.derived_type_id(base, "leaf")
    api.register(
        "base",
        {
            "type": "object",
            "x-gts-abstract": True,
            "x-gts-traits-schema": {
                "type": "object",
                "required": ["selector"],
                "properties": {
                    "selector": {
                        "type": "string",
                        "x-gts-pattern-ref": "/$id",
                        "default": base,
                    },
                },
            },
        },
        schema_dialect,
        type_id=base,
    )
    leaf_schema = {"type": "object", "allOf": [{"$ref": "gts://" + base}]}
    if leaf_overrides_default:
        leaf_schema["x-gts-traits"] = {"selector": leaf}
    api.register("leaf", leaf_schema, schema_dialect, type_id=leaf, validate=False)
    api.check_type_schema(leaf, valid=expected_validity)


# ---------------------------------------------------------------------------
# Registry independence: coverage is decided from the identifiers alone.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["none", "any-present", "any-valid"])
@pytest.mark.parametrize(
    "target_state", ["unregistered", "registered_valid", "registered_invalid"]
)
def test_registry_and_reference_policy_do_not_affect_coverage(
    gts_api, schema_dialect, target_state, mode
):
    """Neither the operand's registry state nor `gts-ref-validation` changes
    the verdict; an empty registry must not make a broad value vacuously
    covered."""
    api = gts_api
    target = api.type_id("target")
    if target_state == "registered_valid":
        api.register("target", {"type": "object"}, schema_dialect, type_id=target)
    elif target_state == "registered_invalid":
        api.register(
            "target",
            {"$ref": "gts://" + api.type_id("missing")},
            schema_dialect,
            type_id=target,
            validate=False,
        )
    holder = api.register(
        "holder",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": target}},
        },
        schema_dialect,
        mode=mode,
    )
    api.check_type_schema(holder, valid=True, mode=mode)
    for name, covered in (
        ("concrete_type", target),
        ("concrete_instance", target + "acme.prod._.uploads.v1"),
        ("wildcard", target + "acme.storage.resources.bucket.*"),
    ):
        instance = api.register_instance(
            holder, {"scope": covered}, name=name, validate=True, mode=mode
        )
        api.check_instance(instance, valid=True, mode=mode)
    for name, rejected in (
        ("broader", target.rsplit(".v", 1)[0] + ".*"),
        ("malformed", target + "**"),
    ):
        # Registration with validation enforces values in every mode (§9.3).
        api.register_instance(
            holder,
            {"scope": rejected},
            name=name,
            validate=True,
            mode=mode,
            status=422,
        )
        instance = api.register_instance(holder, {"scope": rejected}, name=name)
        api.check_instance(instance, valid=False, mode=mode)
    # Invalid instances do not make the holder type itself invalid.
    api.check_type_schema(holder, valid=True, mode=mode)


@pytest.mark.parametrize("mode", ["none", "any-present", "any-valid"])
def test_relationship_discovery_does_not_affect_pattern_validation(
    gts_api, schema_dialect, mode
):
    """Unregistered operands and values remain valid before and after OP#7.

    The specification does not prescribe the discovery algorithm or the
    exact contents of the relationship graph. This test checks
    registry-independent validation (README §9.6.2), not graph contents.
    """
    api = gts_api
    unregistered = api.type_id("unregistered")
    holder = api.register(
        "holder",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {"type": "string", "x-gts-pattern-ref": unregistered},
            },
        },
        schema_dialect,
        mode=mode,
    )
    instance = api.register_instance(
        holder,
        {"scope": unregistered + "acme.prod._.uploads.v1"},
        validate=True,
        mode=mode,
    )
    api.check_type_schema(holder, valid=True, mode=mode)
    api.check_instance(instance, valid=True, mode=mode)
    for entity_id in (holder, instance):
        api.request("GET", "/resolve-relationships", params={"gts_id": entity_id})
    api.check_type_schema(holder, valid=True, mode=mode)
    api.check_instance(instance, valid=True, mode=mode)
