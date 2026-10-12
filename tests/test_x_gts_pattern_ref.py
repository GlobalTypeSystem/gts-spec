"""x-gts-pattern-ref conformance tests (README §9.6.2, §10; ADR-0007).

Each test registers a schema whose `scope` property carries the keyword and
validates payloads against it. Coverage expectations and negative witnesses
are explicit test data. The offline recognizer in
test_gts_id_pattern_syntax_unit.py checks their syntax only; it does not
implement coverage.
"""

import pytest

# The longest valid value: 1024 characters, including the `*`.
_LONGEST_PATTERN = "gts." + "a" * 1018 + ".*"

# Canonical identifiers have at most 1024 characters (§2.1), so a valid pattern
# can select none of them: then M(p) is empty and every operand covers p. A
# wildcard after the vendor token needs at least `a._.a.v0~` (a first segment
# is a type), one after the version marker at least `0~`. Each pair below sits
# on either side of that bound; witnesses have exactly 1024 characters.
_EMPTY_VENDOR_PATTERN = "gts." + "a" * 1011 + ".*"
_EMPTY_VENDOR_COMPLETION = "gts." + "a" * 1011 + ".a._.a.v0~"
_VENDOR_PATTERN = "gts." + "a" * 1010 + ".*"
_VENDOR_WITNESS = "gts." + "a" * 1010 + ".a._.a.v0~"
_EMPTY_VERSION_PATTERN = "gts." + "a" * 1011 + ".b.c.d.v*"
_EMPTY_VERSION_COMPLETION = "gts." + "a" * 1011 + ".b.c.d.v0~"
_VERSION_PATTERN = "gts." + "a" * 1010 + ".b.c.d.v*"
_VERSION_WITNESS = "gts." + "a" * 1010 + ".b.c.d.v0~"

_UUID = "7a1d2f34-5678-49ab-9012-abcdef123456"

VALID_PATTERNS = (
    pytest.param("gts.*", id="any"),
    pytest.param("gts.x.*", id="vendor"),
    pytest.param("gts.x.core.*", id="package"),
    pytest.param("gts.x.core.events.*", id="namespace"),
    pytest.param("gts.x.core.events.type.*", id="type"),
    pytest.param("gts.x.core.events.type.v*", id="version_marker"),
    pytest.param("gts.x.core.events.type.v1.*", id="major"),
    pytest.param("gts.x.core.events.type.v0.*", id="major_zero"),
    pytest.param("gts.x.core.events.type.v1~*", id="chain"),
    pytest.param("gts.x.core.events.type.v1.0~*", id="chain_minor"),
    pytest.param("gts.x.core.events.type.v1~xyz.*", id="chain_vendor"),
    pytest.param("gts.x.core.events.type.v1~x.y._.w.v1.*", id="chain_major"),
    pytest.param(
        "gts.x.core.events.type.v1~x.core._.audit_event.v1~xyz.app.*",
        id="chain_two_types",
    ),
    pytest.param("gts.x.core.events.type.v1~", id="concrete_type"),
    pytest.param("gts.x.core.events.type.v1.2~", id="concrete_type_minor"),
    pytest.param(
        "gts.x.core.events.type.v1~ven.app._.custom_event.v1~",
        id="concrete_chained_type",
    ),
    pytest.param(
        "gts.x.core.events.topic.v1~ven.app._.custom_event_topic.v1.2",
        id="concrete_well_known_instance",
    ),
    pytest.param(
        "gts.x.core.events.type.v1~7a1d2f34-5678-49ab-9012-abcdef123456",
        id="concrete_anonymous_instance",
    ),
    pytest.param("gts.nobody.unregistered.*", id="unregistered_prefix"),
    pytest.param(_LONGEST_PATTERN, id="length_1024"),
    pytest.param(_VENDOR_WITNESS, id="concrete_length_1024"),
    pytest.param("gts.x.core.resources.resource.v" + "9" * 80 + "~", id="large_major"),
    pytest.param(
        "gts.x.core.resources.resource.v1." + "9" * 80 + "~", id="large_minor"
    ),
    pytest.param(
        "gts.x.core.resources.resource.v" + "9" * 80 + ".*", id="large_major_wildcard"
    ),
)

INVALID_PATTERNS = (
    pytest.param("", id="empty"),
    pytest.param("*", id="bare_wildcard"),
    pytest.param("gts", id="prefix_without_dot"),
    pytest.param("gts.", id="prefix_only"),
    pytest.param("gts*", id="wildcard_in_prefix"),
    pytest.param("gts.vendor*", id="partial_vendor"),
    pytest.param("gts.x.core.events.type.v1*", id="partial_major"),
    pytest.param("gts.x.core.events.type.v1.0*", id="partial_minor"),
    pytest.param("gts.x.core.events.type.v1.0.*", id="after_minor"),
    pytest.param("gts.x.core.events.type.v1~abc*", id="partial_chain_vendor"),
    pytest.param("gts.x.core.events.type.vx.*", id="bad_major"),
    pytest.param("gts.x.*.events.type.v1~", id="wildcard_in_middle"),
    pytest.param("gts.x.core.*~*", id="two_wildcards"),
    pytest.param("gts.x.llm.chat.message.v*~*", id="two_wildcards_version"),
    pytest.param("gts.x.core.events.type.v1~**", id="double_wildcard"),
    pytest.param("gts.x.core.events.type.v1~*~", id="wildcard_not_last"),
    pytest.param("gts.x.core.events.type.v1~x.y._.w.v1@name", id="attribute"),
    pytest.param('gts.x.core.events.type.v1~[name="x"]', id="query"),
    pytest.param("gts.x.core.events.type.v1~550e8400-*", id="partial_uuid"),
    pytest.param("gts.x.core.events.type.v1~" + _UUID + "*", id="wildcard_after_uuid"),
    pytest.param("gts.x.core.events.type.v1~" + _UUID + "~", id="tilde_after_uuid"),
    pytest.param("gts.x.core.events.type.v1~" + _UUID + "~*", id="chain_after_uuid"),
    pytest.param(
        "gts.x.core.events.type.v1~7A1D2F34-5678-49AB-9012-ABCDEF123456",
        id="uppercase_uuid",
    ),
    pytest.param("GTS.x.core.*", id="uppercase_prefix"),
    pytest.param("gts.X.core.*", id="uppercase_token"),
    pytest.param(" gts.x.core.*", id="leading_space"),
    pytest.param("gts.x.core.* ", id="trailing_space"),
    pytest.param("gts.x.core.events.type.v1~\n", id="trailing_lf"),
    pytest.param("gts.x.core.events.type.v1~\r", id="trailing_cr"),
    pytest.param("gts.x.core.events.type.v1~\u2028", id="trailing_unicode_separator"),
    pytest.param("gts.x. core.*", id="inner_space"),
    pytest.param("gts://gts.x.core.events.type.v1~", id="uri_form"),
    pytest.param("gts://gts.*", id="uri_form_wildcard"),
    pytest.param("gts.x.core.events.type.v1", id="single_segment_instance"),
    pytest.param("gts.x.core.events.type.v01~", id="major_leading_zero"),
    pytest.param("gts.x.core.events.type.v1.01~*", id="minor_leading_zero"),
    pytest.param("gts.x.core.events.type~", id="missing_version"),
    pytest.param("gts.x.core.events.type.v1~~", id="double_tilde"),
    pytest.param("gts.x.core-1.events.*", id="hyphen"),
    pytest.param("gts.1x.core.*", id="token_starts_with_digit"),
    pytest.param("gts.x.сore.*", id="non_ascii"),
    pytest.param("gts." + "a" * 1019 + ".*", id="length_1025"),
    pytest.param(_EMPTY_VENDOR_COMPLETION, id="concrete_length_1025"),
)


FAMILY = "gts.x.core.resources.resource.*"
RESOURCE = "gts.x.core.resources.resource.v1~"
BUCKET = RESOURCE + "acme.storage.resources.bucket.v1~"
BUCKET_FAMILY = RESOURCE + "acme.storage.resources.bucket.*"
INSTANCE = BUCKET + "acme.prod._.uploads.v1"
ANONYMOUS = RESOURCE + "7a1d2f34-5678-49ab-9012-abcdef123456"
OTHER = "gts.x.core.events.event.*"

# (operand, value): every identifier the value selects, the operand selects too.
COVERED_CASES = (
    pytest.param(_LONGEST_PATTERN, _LONGEST_PATTERN, id="operand_length_1024"),
    pytest.param(
        "gts.x.core.resources.resource.v" + "9" * 80 + "~",
        "gts.x.core.resources.resource.v" + "9" * 80 + "~",
        id="large_operand_version",
    ),
    pytest.param(FAMILY, FAMILY, id="equal_wildcards"),
    pytest.param(FAMILY, RESOURCE, id="family_covers_type"),
    pytest.param(FAMILY, BUCKET_FAMILY, id="family_covers_derived_pattern"),
    pytest.param(FAMILY, INSTANCE, id="family_covers_instance"),
    pytest.param(RESOURCE, RESOURCE, id="type_covers_self"),
    pytest.param(RESOURCE, RESOURCE + "*", id="type_covers_suffix_wildcard"),
    pytest.param(RESOURCE + "*", RESOURCE, id="suffix_wildcard_covers_type"),
    pytest.param(RESOURCE, BUCKET_FAMILY, id="type_covers_derived_pattern"),
    pytest.param(RESOURCE, INSTANCE, id="type_covers_instance"),
    pytest.param(RESOURCE, ANONYMOUS, id="type_covers_anonymous_instance"),
    pytest.param(RESOURCE, "gts.x.core.resources.resource.v1.2~", id="omitted_minor"),
    pytest.param(
        "gts.x.core.resources.resource.v1.*",
        RESOURCE,
        id="first_segment_major_covers_type",
    ),
    pytest.param(
        RESOURCE,
        "gts.x.core.resources.resource.v1.*",
        id="first_segment_major_equivalent",
    ),
    pytest.param(RESOURCE + "acme.*", BUCKET_FAMILY, id="chain_vendor_scope"),
    pytest.param(
        BUCKET,
        RESOURCE + "acme.storage.resources.bucket.v1.2~",
        id="derived_minor_flexibility",
    ),
    pytest.param(
        RESOURCE + "acme.storage.resources.bucket.v1.*",
        BUCKET,
        id="later_major_covers_type",
    ),
    pytest.param(INSTANCE, INSTANCE, id="exact_instance"),
    pytest.param(ANONYMOUS, ANONYMOUS, id="exact_uuid_instance"),
    pytest.param(
        BUCKET,
        "gts.x.core.resources.resource.v1.2~acme.storage.resources.bucket.v1~",
        id="earlier_segment_minor_flexibility",
    ),
    pytest.param(
        FAMILY, "gts.x.core.resources.resource.v*", id="version_marker_equivalent"
    ),
    pytest.param(
        "gts.x.core.resources.resource.v*",
        FAMILY,
        id="version_marker_equivalent_reverse",
    ),
    pytest.param(
        RESOURCE,
        "gts.x.core.resources.resource.v1." + "9" * 80 + "~",
        id="large_minor_flexibility",
    ),
    # A value whose every completion exceeds 1024 characters selects nothing.
    pytest.param(FAMILY, _LONGEST_PATTERN, id="empty_value_longest"),
    pytest.param(FAMILY, _EMPTY_VENDOR_PATTERN, id="empty_value_vendor"),
    pytest.param(FAMILY, _EMPTY_VERSION_PATTERN, id="empty_value_version_marker"),
    pytest.param(
        _EMPTY_VENDOR_PATTERN,
        "gts." + "a" * 1012 + ".*",
        id="empty_operand_covers_empty_value",
    ),
)

# (operand, value, witness): the witness is a canonical identifier that the
# value selects and the operand does not.
UNCOVERED_CASES = (
    pytest.param(
        RESOURCE,
        FAMILY,
        "gts.x.core.resources.resource.v2~",
        id="broader_major_scope",
    ),
    pytest.param(
        FAMILY,
        "gts.x.core.resources.*",
        "gts.x.core.resources.other.v1~",
        id="broader_namespace",
    ),
    pytest.param(FAMILY, OTHER, "gts.x.core.events.event.v1~", id="other_family"),
    pytest.param(
        FAMILY,
        "gts.x.core.resources.resource_extra.*",
        "gts.x.core.resources.resource_extra.v1~",
        id="type_token_boundary",
    ),
    pytest.param(
        RESOURCE,
        "gts.x.core.resources.resource.v10~",
        "gts.x.core.resources.resource.v10~",
        id="major_boundary",
    ),
    pytest.param(
        "gts.x.core.resources.resource.v1.2~",
        RESOURCE,
        "gts.x.core.resources.resource.v1.3~",
        id="explicit_minor_rejects_flexible",
    ),
    pytest.param(
        "gts.x.core.resources.resource.v1.2~",
        "gts.x.core.resources.resource.v1.3~",
        "gts.x.core.resources.resource.v1.3~",
        id="different_minor",
    ),
    pytest.param(
        RESOURCE + "acme.*", RESOURCE, RESOURCE, id="chain_prefix_requires_suffix"
    ),
    pytest.param(
        BUCKET,
        RESOURCE + "acme.storage.resources.bucket.v1.*",
        RESOURCE + "acme.storage.resources.bucket.v1",
        id="later_major_includes_instance",
    ),
    pytest.param(
        INSTANCE,
        "gts.x.core.resources.resource.v1.0~"
        "acme.storage.resources.bucket.v1~acme.prod._.uploads.v1",
        "gts.x.core.resources.resource.v1.0~"
        "acme.storage.resources.bucket.v1~acme.prod._.uploads.v1",
        id="instance_type_minor_is_exact",
    ),
    pytest.param(
        INSTANCE,
        INSTANCE + ".0",
        INSTANCE + ".0",
        id="instance_has_no_minor_expansion",
    ),
    pytest.param(INSTANCE + ".0", INSTANCE, INSTANCE, id="instance_minor_not_optional"),
    pytest.param(
        INSTANCE, INSTANCE + "0", INSTANCE + "0", id="instance_version_boundary"
    ),
    pytest.param(
        INSTANCE,
        BUCKET + "acme.prod._.uploads.*",
        INSTANCE + "0",
        id="instance_rejects_wildcard",
    ),
    pytest.param(INSTANCE, INSTANCE + "~", INSTANCE + "~", id="instance_rejects_type"),
    pytest.param(
        ANONYMOUS,
        RESOURCE + "7a1d2f34-5678-49ab-9012-abcdef123457",
        RESOURCE + "7a1d2f34-5678-49ab-9012-abcdef123457",
        id="different_uuid",
    ),
    pytest.param("gts.acme.*", BUCKET, BUCKET, id="wildcard_anchors_first_segment"),
    pytest.param(
        "gts.acme.storage.resources.bucket.v1~",
        BUCKET,
        BUCKET,
        id="type_anchors_first_segment",
    ),
    pytest.param(
        "gts.x.core.resources.resource.v1.2~",
        "gts.x.core.resources.resource.v1.20~",
        "gts.x.core.resources.resource.v1.20~",
        id="explicit_minor_boundary",
    ),
    pytest.param(
        "gts.x.core.resources.resource.v1.2~acme.*",
        RESOURCE + "acme.*",
        "gts.x.core.resources.resource.v1.3~acme.x._.y.v1~",
        id="explicit_first_minor_before_wildcard",
    ),
    pytest.param(
        BUCKET + "*",
        RESOURCE + "acme.storage.resources.bucket.v1.*",
        RESOURCE + "acme.storage.resources.bucket.v1",
        id="later_chain_wildcard_excludes_instance",
    ),
    pytest.param(
        "gts.x.core.resources.resource.v" + "9" * 80 + "~",
        "gts.x.core.resources.resource.v" + "9" * 79 + "8~",
        "gts.x.core.resources.resource.v" + "9" * 79 + "8~",
        id="large_majors_differ",
    ),
    # The neighbours of the empty-selection boundary select a 1024-character ID.
    pytest.param(FAMILY, _VENDOR_PATTERN, _VENDOR_WITNESS, id="nonempty_value_vendor"),
    pytest.param(
        FAMILY,
        _VERSION_PATTERN,
        _VERSION_WITNESS,
        id="nonempty_value_version_marker",
    ),
    # An operand that selects nothing covers only values that select nothing.
    pytest.param(_LONGEST_PATTERN, RESOURCE, RESOURCE, id="empty_operand"),
)


# ---------------------------------------------------------------------------
# Syntax: `gts.*` accepts every well-formed pattern and nothing else.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", VALID_PATTERNS)
def test_universal_operand_accepts_valid_pattern(gts_api, schema_dialect, value):
    """A well-formed GTS ID or wildcard pattern is covered by `gts.*`; `not`
    inverts the verdict."""
    api = gts_api
    scope_type = api.register(
        "scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": "gts.*"}},
        },
        schema_dialect,
    )
    negated_scope_type = api.register(
        "negated_scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "type": "string",
                    "not": {"type": "string", "x-gts-pattern-ref": "gts.*"},
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(scope_type, {"scope": value}, valid=True)
    api.check_payload(negated_scope_type, {"scope": value}, valid=False)


@pytest.mark.parametrize("value", INVALID_PATTERNS)
def test_universal_operand_rejects_invalid_pattern(gts_api, schema_dialect, value):
    """A malformed value fails `x-gts-pattern-ref: gts.*`, so its negation
    succeeds: a syntax failure is an ordinary validation failure."""
    api = gts_api
    scope_type = api.register(
        "scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": "gts.*"}},
        },
        schema_dialect,
    )
    negated_scope_type = api.register(
        "negated_scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "type": "string",
                    "not": {"type": "string", "x-gts-pattern-ref": "gts.*"},
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(scope_type, {"scope": value}, valid=False)
    api.check_payload(negated_scope_type, {"scope": value}, valid=True)


# ---------------------------------------------------------------------------
# Coverage: a value is valid when the operand selects everything it selects.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("operand,value", COVERED_CASES)
def test_covered_value_is_accepted(gts_api, schema_dialect, operand, value):
    """The operand selects every identifier the value selects (§10)."""
    api = gts_api
    scope_type = api.register(
        "scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": operand}},
        },
        schema_dialect,
    )
    negated_scope_type = api.register(
        "negated_scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "type": "string",
                    "not": {"type": "string", "x-gts-pattern-ref": operand},
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(scope_type, {"scope": value}, valid=True)
    api.check_payload(negated_scope_type, {"scope": value}, valid=False)


@pytest.mark.parametrize("operand,value,witness", UNCOVERED_CASES)
def test_uncovered_value_is_rejected(gts_api, schema_dialect, operand, value, witness):
    """The value selects the witness, which the operand does not select."""
    api = gts_api
    scope_type = api.register(
        "scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": operand}},
        },
        schema_dialect,
    )
    negated_scope_type = api.register(
        "negated_scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "type": "string",
                    "not": {"type": "string", "x-gts-pattern-ref": operand},
                },
            },
        },
        schema_dialect,
    )
    api.check_payload(scope_type, {"scope": value}, valid=False)
    api.check_payload(negated_scope_type, {"scope": value}, valid=True)

    # The witness proves the verdict: the value's own scope accepts it ...
    value_scope_type = api.register(
        "value_scope",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": {"type": "string", "x-gts-pattern-ref": value}},
        },
        schema_dialect,
    )
    api.check_payload(value_scope_type, {"scope": witness}, valid=True)
    # ... and the operand's scope rejects it.
    api.check_payload(scope_type, {"scope": witness}, valid=False)


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


INVALID_OPERANDS = (
    pytest.param(None, id="null"),
    pytest.param(True, id="boolean"),
    pytest.param(3, id="number"),
    pytest.param([], id="array"),
    pytest.param({}, id="object"),
    pytest.param("", id="empty"),
    pytest.param("gts.vendor*", id="partial_token"),
    pytest.param("gts.x.core.resources.resource.v01~", id="leading_zero"),
    pytest.param("gts://" + RESOURCE, id="uri"),
    pytest.param(FAMILY + " ", id="whitespace"),
    pytest.param("gts." + "a" * 1019 + ".*", id="length_1025"),
    pytest.param("/", id="root_pointer"),
    pytest.param("/$schema", id="schema_pointer"),
    pytest.param("/properties/value", id="property_pointer"),
    pytest.param("/$id/", id="extended_self_pointer"),
)


@pytest.mark.parametrize("operand", INVALID_OPERANDS)
def test_invalid_operand_is_not_inverted(gts_api, schema_dialect, operand):
    """`not` around an invalid operand is still a schema error, never a match."""
    assert_schema_error_everywhere(
        gts_api,
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
            [case.values[0] for case in VALID_PATTERNS], True, id="valid_corpus"
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
def test_trait_syntax_corpus(gts_api, schema_dialect, trait_values, expected_validity):
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


def test_patterns_do_not_create_relationships(gts_api, schema_dialect):
    """An operand is not reported as an OP#7 relationship (README §9.2).

    The API declares the OP#7 response only as an object. ``refs`` is the
    relationship map of the reference implementation's graph: this assertion
    depends on that shape, an existing contract limitation, until the API
    defines one. Diagnostics are not relationships and are not compared.
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
    )
    api.check_type_schema(holder, valid=True)
    graph = api.request("GET", "/resolve-relationships", params={"gts_id": holder})
    assert graph["id"] == holder, graph
    assert not graph.get("refs"), graph
