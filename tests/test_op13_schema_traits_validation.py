import pytest

from .conftest import get_gts_base_url
from .helpers.http_client import get_session
from .helpers.http_run_helpers import (
    register as _register,
    register_derived as _register_derived,
    register_abstract as _register_abstract,
    register_instance as _register_instance,
    validate_entity as _validate_entity,
    validate_instance as _validate_instance,
    validate_type_schema as _validate_type_schema,
)
from httprunner import HttpRunner, Config, RunRequest, Step


def _register_bulk(schema_body, label):
    return Step(
        RunRequest(label)
        .post("/entities/bulk")
        .with_json([schema_body])
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", True)
    )


# Note (v0.12): ADR-0003 keys trait-completeness on x-gts-abstract (not "leaf").
# Refimpls remain permissive at POST /entities — completeness is verified at
# POST /validate-type-schema. New ADR-0003/0004 cases below follow that pattern.


@pytest.fixture(scope="module", autouse=True)
def seed_shared_topic_ref_registry():
    entities = (
        {
            "$id": "gts://gts.x.test13.events.topic.v1~",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
            },
        },
        {
            "id": "gts.x.test13.events.topic.v1~x.test13._.orders.v1",
            "name": "orders",
        },
        {
            "id": "gts.x.test13.events.topic.v1~x.core._.default.v1",
            "name": "default",
        },
        {
            "id": "gts.x.test13.events.topic.v1~x.test13._.custom.v1",
            "name": "custom",
        },
        {
            "id": "gts.x.test13.events.topic.v1~x.test13._.audit.v1",
            "name": "audit",
        },
    )
    for entity in entities:
        response = get_session().post(
            f"{get_gts_base_url()}/entities", json=entity, timeout=30
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCaseOp13_Seed_TopicRefRegistry(HttpRunner):
    """Seed shared x-gts-ref targets for the OP#13 trait tests.

    Many trait tests below annotate a `topicRef` trait with
    `x-gts-ref: "gts.x.test13.events.topic.v1~"` and supply concrete topic
    references as trait values. Under §9.6 a *specific* (non-wildcard)
    `x-gts-ref` is existence-enforced: the concrete constraint type and each
    referenced value MUST be registered, or validation fails. Their validity is
    outside x-gts-ref validation. This class registers the topic type and every
    topic instance those tests reference so their `x-gts-ref` values resolve. It
    runs first (file order), and the entries persist for the rest of the session.
    """

    config = Config("OP#13 - Seed topicRef registry").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.events.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic type schema (x-gts-ref target)",
        ),
        _register_instance(
            {
                "id": "gts.x.test13.events.topic.v1~x.test13._.orders.v1",
                "name": "orders",
            },
            "register topic instance (orders)",
        ),
        _register_instance(
            {
                "id": "gts.x.test13.events.topic.v1~x.core._.default.v1",
                "name": "default",
            },
            "register topic instance (default) referenced by trait-schema defaults",
        ),
        _register_instance(
            {
                "id": "gts.x.test13.events.topic.v1~x.test13._.custom.v1",
                "name": "custom",
            },
            "register topic instance (custom)",
        ),
        _register_instance(
            {
                "id": "gts.x.test13.events.topic.v1~x.test13._.audit.v1",
                "name": "audit",
            },
            "register topic instance (audit)",
        ),
    ]


class TestCaseOp13_TraitsValid_AllResolved(HttpRunner):
    """OP#13 - Traits: derived schema provides all trait values.

    Validation passes.
    """
    config = Config("OP#13 - All Traits Resolved").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.traits.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "description": "Topic reference",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                            "description": "Retention period",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with traits-schema (no defaults)",
        ),
        _register_derived(
            "gts://gts.x.test13.traits.event.v1~x.test13._.order_event.v1~",
            "gts://gts.x.test13.traits.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                    "retention": "P90D",
                },
            },
            "register derived with all traits resolved",
        ),
        _validate_type_schema(
            "gts.x.test13.traits.event.v1~x.test13._.order_event.v1~",
            True,
            "validate derived - all traits resolved",
        ),
    ]


class TestCaseOp13_TraitsValid_DefaultsUsed(HttpRunner):
    """OP#13 - Traits: base provides defaults, derived omits them - passes"""
    config = Config("OP#13 - Traits Defaults Used").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.dfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                            "default": (
                                "gts.x.test13.events.topic.v1~"
                                "x.core._.default.v1"
                            ),
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with traits-schema (all defaults)",
        ),
        _register_derived(
            "gts://gts.x.test13.dfl.event.v1~x.test13._.simple_event.v1~",
            "gts://gts.x.test13.dfl.event.v1~",
            {
                "type": "object",
            },
            "register derived with no x-gts-traits (rely on defaults)",
        ),
        _validate_type_schema(
            "gts.x.test13.dfl.event.v1~x.test13._.simple_event.v1~",
            True,
            "validate derived - defaults fill all traits",
        ),
    ]


class TestCaseOp13_TraitsInvalid_MissingRequired(HttpRunner):
    """OP#13 - Traits: trait property has no default.

    Derived omits it - fails.
    """
    config = Config("OP#13 - Missing Required Trait").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.miss.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "description": "Required - no default",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                    "required": ["topicRef"],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with one required trait without default",
        ),
        _register_derived(
            "gts://gts.x.test13.miss.event.v1~x.test13._.incomplete.v1~",
            "gts://gts.x.test13.miss.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P90D",
                },
            },
            "register derived missing topicRef trait",
        ),
        _validate_type_schema(
            "gts.x.test13.miss.event.v1~x.test13._.incomplete.v1~",
            False,
            "validate should fail - topicRef not resolved",
        ),
    ]


class TestCaseOp13_TraitsInvalid_WrongType(HttpRunner):
    """OP#13 - Traits: trait value violates trait schema type - fails"""
    config = Config("OP#13 - Trait Value Wrong Type").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.wtype.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "maxRetries": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 3,
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with integer trait",
        ),
        _register_derived(
            "gts://gts.x.test13.wtype.event.v1~x.test13._.bad_type.v1~",
            "gts://gts.x.test13.wtype.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "maxRetries": "not_a_number",
                    "retention": "P90D",
                },
            },
            "register derived with wrong type for maxRetries",
        ),
        _validate_type_schema(
            "gts.x.test13.wtype.event.v1~x.test13._.bad_type.v1~",
            False,
            "validate should fail - maxRetries is not integer",
        ),
    ]


class TestCaseOp13_TraitRef_AbstractRefConstraintMissing(HttpRunner):
    """Abstract types are exempt from trait *completeness* (§9.7.5) but NOT from
    x-gts-ref reference integrity.

    Per §9.7.5 the completeness check (standard JSON Schema validation of the
    materialized traits) is skipped for x-gts-abstract types; the separate
    "reference resolution of trait values" rule does NOT exempt abstract types.
    An unregistered constraint therefore passes in ``none`` mode and fails in
    ``any-present`` and ``any-valid`` modes, even though a descendant may later supply
    its own x-gts-ref value.
    """
    config = Config(
        "OP#13 x-gts-ref: abstract still validates missing constraint type"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # NOTE: the topic constraint type is intentionally NOT registered.
        _register_abstract(
            "gts://gts.x.test13.absref.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.absref.topic.v1~",
                        },
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base whose x-gts-ref names an unregistered topic type",
        ),
        _validate_type_schema(
            "gts.x.test13.absref.event.v1~",
            True,
            "none mode ignores abstract constraint target presence",
            gts_ref_validation="none",
        ),
        _validate_type_schema(
            "gts.x.test13.absref.event.v1~",
            False,
            "any-present mode rejects missing abstract constraint target",
            gts_ref_validation="any-present",
        ),
        _validate_type_schema(
            "gts.x.test13.absref.event.v1~",
            False,
            "any-valid mode rejects missing abstract constraint target",
            gts_ref_validation="any-valid",
        ),
    ]


class TestCaseOp13_TraitRef_AbstractRefConstraintResolved(HttpRunner):
    """Abstract type declaring an x-gts-ref whose constraint type IS registered,
    and supplying no value, MUST pass.

    Guards against over-strictness: an abstract type must not fail merely for
    declaring an optional x-gts-ref trait it leaves unresolved (completeness is
    skipped) as long as the constraint type it names exists.
    """
    config = Config(
        "OP#13 x-gts-ref: abstract with resolved constraint, no value, passes"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.absrefok.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic constraint type",
        ),
        _register_abstract(
            "gts://gts.x.test13.absrefok.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.absrefok.topic.v1~",
                        },
                    },
                    "required": ["topicRef"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base: required topicRef left unresolved, constraint exists",
        ),
        _validate_type_schema(
            "gts.x.test13.absrefok.event.v1~",
            True,
            "validate should pass - completeness skipped for abstract, "
            "x-gts-ref constraint type is registered, no value to resolve",
        ),
    ]


class TestCaseOp13_TraitRef_AbstractRefValueUnregistered(HttpRunner):
    """Exercise all modes for an abstract type's unregistered trait target.

    Abstract completeness does not change the selected x-gts-ref validation
    mode: ``none`` skips lookup, while ``any-present`` and ``any-valid`` require it.
    """
    config = Config(
        "OP#13 x-gts-ref: abstract resolves declared trait ref values"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.absrefv.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic constraint type",
        ),
        # NOTE: no topic instance is registered, so the declared value dangles.
        _register_abstract(
            "gts://gts.x.test13.absrefv.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.absrefv.topic.v1~",
                        },
                    },
                },
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.absrefv.topic.v1~"
                        "x.test13._.ghost.v1"
                    ),
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base declaring a topicRef value to an unregistered topic",
        ),
        _validate_type_schema(
            "gts.x.test13.absrefv.event.v1~",
            True,
            "none mode ignores missing abstract trait target",
            gts_ref_validation="none",
        ),
        _validate_type_schema(
            "gts.x.test13.absrefv.event.v1~",
            False,
            "any-present mode rejects missing abstract trait target",
            gts_ref_validation="any-present",
        ),
        _validate_type_schema(
            "gts.x.test13.absrefv.event.v1~",
            False,
            "any-valid mode rejects missing abstract trait target",
            gts_ref_validation="any-valid",
        ),
    ]


class TestCaseOp13_TraitRef_AbstractRefValueValidationModes(HttpRunner):
    """Exercise all modes for a present but invalid abstract trait target."""

    config = Config(
        "OP#13 x-gts-ref: present invalid trait target by mode"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.absrefpresent.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic constraint type",
        ),
        _register_instance(
            {
                "id": (
                    "gts.x.test13.absrefpresent.topic.v1~"
                    "x.test13._.invalid.v1"
                ),
            },
            "register invalid topic instance without required name",
        ),
        _validate_instance(
            (
                "gts.x.test13.absrefpresent.topic.v1~"
                "x.test13._.invalid.v1"
            ),
            False,
            "validate topic target - required name is missing",
        ),
        _register_abstract(
            "gts://gts.x.test13.absrefpresent.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.absrefpresent.topic.v1~",
                        },
                    },
                },
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.absrefpresent.topic.v1~"
                        "x.test13._.invalid.v1"
                    ),
                },
                "properties": {"id": {"type": "string"}},
            },
            "register abstract type referring to present invalid topic",
        ),
        _validate_type_schema(
            "gts.x.test13.absrefpresent.event.v1~",
            True,
            "none mode ignores invalid abstract trait target",
            gts_ref_validation="none",
        ),
        _validate_type_schema(
            "gts.x.test13.absrefpresent.event.v1~",
            True,
            "any-present mode accepts present invalid abstract trait target",
            gts_ref_validation="any-present",
        ),
        _validate_type_schema(
            "gts.x.test13.absrefpresent.event.v1~",
            False,
            "any-valid mode rejects invalid abstract trait target",
            gts_ref_validation="any-valid",
        ),
    ]


class TestCaseOp13_TraitsInvalid_UnknownProperty(HttpRunner):
    """OP#13 - Traits: trait value includes unknown property.

    additionalProperties false - fails.
    """
    config = Config("OP#13 - Unknown Trait Property").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.unk.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with closed traits-schema",
        ),
        _register_derived(
            "gts://gts.x.test13.unk.event.v1~x.test13._.extra_trait.v1~",
            "gts://gts.x.test13.unk.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P90D",
                    "unknownTrait": "some_value",
                },
            },
            "register derived with unknown trait property",
        ),
        _validate_type_schema(
            "gts.x.test13.unk.event.v1~x.test13._.extra_trait.v1~",
            False,
            "validate should fail - unknownTrait not in schema",
        ),
    ]


class TestCaseOp13_TraitsValid_PartialOverride(HttpRunner):
    """OP#13 - Traits: derived overrides one trait.

    Other uses default - passes.
    """
    config = Config("OP#13 - Partial Override With Defaults").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.part.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                            "default": (
                                "gts.x.test13.events.topic.v1~"
                                "x.core._.default.v1"
                            ),
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with all defaults",
        ),
        _register_derived(
            "gts://gts.x.test13.part.event.v1~x.test13._.partial.v1~",
            "gts://gts.x.test13.part.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.custom.v1"
                    ),
                },
            },
            "register derived overriding only topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.part.event.v1~x.test13._.partial.v1~",
            True,
            "validate - topicRef overridden, retention uses default",
        ),
    ]


class TestCaseOp13_TraitsValid_BothKeywordsInSameSchema(HttpRunner):
    """OP#13 - Traits: mid-level schema has both x-gts-traits-schema.

    And x-gts-traits.
    """
    config = Config("OP#13 - Both Keywords Same Schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.both.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with traits-schema",
        ),
        _register_derived(
            "gts://gts.x.test13.both.event.v1~x.test13._.audit.v1~",
            "gts://gts.x.test13.both.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "auditRetention": {
                            "type": "string",
                            "default": "P365D",
                        },
                    },
                },
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.audit.v1"
                    ),
                },
            },
            "register mid-level with both keywords",
        ),
        _validate_type_schema(
            "gts.x.test13.both.event.v1~x.test13._.audit.v1~",
            True,
            "validate mid-level - topicRef resolved, retention has default",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.both.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.login_audit.v1~"
            ),
            "gts://gts.x.test13.both.event.v1~x.test13._.audit.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "auditRetention": "P730D",
                },
            },
            "register leaf resolving auditRetention",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.both.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.login_audit.v1~"
            ),
            True,
            "validate leaf - all traits resolved across chain",
        ),
    ]


class TestCaseOp13_TraitsInvalid_3Level_MissingInLeaf(HttpRunner):
    """OP#13 - Traits: 3-level chain.

    Leaf missing trait from mid-level schema - fails.
    """
    config = Config("OP#13 - 3-Level Missing Trait In Leaf").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.l3miss.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base",
        ),
        _register_derived(
            "gts://gts.x.test13.l3miss.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.l3miss.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "description": "No default - must be resolved",
                        },
                    },
                    "required": ["priority"],
                },
            },
            "register mid-level adding required priority trait (no default)",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.l3miss.event.v1~"
                "x.test13._.mid.v1~"
                "x.test13._.leaf_missing.v1~"
            ),
            "gts://gts.x.test13.l3miss.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P90D",
                },
            },
            "register leaf missing priority trait",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.l3miss.event.v1~"
                "x.test13._.mid.v1~"
                "x.test13._.leaf_missing.v1~"
            ),
            False,
            "validate should fail - priority not resolved",
        ),
    ]


# NOTE (v0.12): three classes that asserted "MUST fail on override" were
# removed:
# - TraitsInvalid_OverrideInChain          (value override)
# - TraitsInvalid_OverrideTopicRef3Level   (value override)
# - TraitsInvalid_ChangeDefaultInMid       (default override in trait-schema)
#
# Rationale: ADR-0004 adopts RFC 7396 JSON Merge Patch for trait VALUES
# (descendant last-wins, no GTS-specific immutability). The same extension
# narrative — "narrowing is about validation surface; rely on standard JSON
# Schema; lock with `const`" — applies to trait-schema `default`s: defaults
# are annotations and do not participate in narrowing (see §9.7.5). A
# descendant MAY redeclare a property's `default`; the effective default at
# materialization time is the leaf-most one along the chain. To lock a value
# across descendants, use `const`.
#
# Replacement coverage:
# - Value overrides: TestCaseOp13_Merge_* below.
# - Default redeclaration: TestCaseOp13_TraitsSchema_RedeclareDefaultAllowed
#   below, paired with the existing TestCaseOp13_Merge_ConstLock_* tests for
#   the `const`-based locking pattern.


class TestCaseOp13_TraitsSchema_RedeclareDefaultAllowed(HttpRunner):
    """ADR-0002 / §9.7.5: descendant redeclares a trait-schema `default`.

    Base declares `retention.default = "P30D"`. Mid-level descendant
    redeclares `retention.default = "P90D"`. Neither layer supplies a value
    in `x-gts-traits`. Validation MUST pass — defaults are annotations and
    do not participate in narrowing. At materialization, the leaf-most
    declared default ("P90D") fills the absent key.
    """
    config = Config(
        "OP#13 ADR-0002: redeclare trait-schema default allowed"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.rdfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with retention default=P30D",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.rdfl.event.v1~"
                "x.test13._.rdfl_mid.v1~"
            ),
            "gts://gts.x.test13.rdfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {
                            "type": "string",
                            "default": "P90D",
                        },
                    },
                },
            },
            "register mid redeclaring retention default to P90D",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.rdfl.event.v1~"
                "x.test13._.rdfl_mid.v1~"
            ),
            True,
            "validate - default redeclaration is allowed",
        ),
    ]


class TestCaseOp13_TraitsInvalid_ConstraintViolation(HttpRunner):
    """OP#13 - Traits: trait value violates enum constraint.

    In trait schema - fails.
    """
    config = Config("OP#13 - Trait Constraint Violation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.enum.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "default": "medium",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with enum-constrained trait",
        ),
        _register_derived(
            "gts://gts.x.test13.enum.event.v1~x.test13._.bad_enum.v1~",
            "gts://gts.x.test13.enum.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "priority": "ultra_high",
                    "retention": "P90D",
                },
            },
            "register derived with invalid enum value",
        ),
        _validate_type_schema(
            "gts.x.test13.enum.event.v1~x.test13._.bad_enum.v1~",
            False,
            "validate should fail - priority not in enum",
        ),
    ]


class TestCaseOp13_TraitsValid_ValidateEntity(HttpRunner):
    """OP#13 - Traits: validate-entity endpoint also checks traits"""
    config = Config("OP#13 - Validate Entity With Traits").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.ent.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base",
        ),
        _register_derived(
            "gts://gts.x.test13.ent.event.v1~x.test13._.good_ent.v1~",
            "gts://gts.x.test13.ent.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                    "retention": "P90D",
                },
            },
            "register derived with traits",
        ),
        _validate_entity(
            "gts.x.test13.ent.event.v1~x.test13._.good_ent.v1~",
            True,
            "validate-entity should pass",
            expected_entity_type="schema",
        ),
    ]


class TestCaseOp13_TraitsInvalid_ValidateEntity_MissingTrait(HttpRunner):
    """OP#13 - Traits: validate-entity catches missing trait"""
    config = Config("OP#13 - Validate Entity Missing Trait").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.entm.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                        },
                    },
                    "required": ["topicRef", "retention"],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base (no defaults, both traits required)",
        ),
        _register_derived(
            "gts://gts.x.test13.entm.event.v1~x.test13._.bad_ent.v1~",
            "gts://gts.x.test13.entm.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                },
            },
            "register derived missing retention",
        ),
        _validate_entity(
            "gts.x.test13.entm.event.v1~x.test13._.bad_ent.v1~",
            False,
            "validate-entity should fail - retention not resolved",
            expected_entity_type="schema",
        ),
    ]


class TestCaseOp13_TraitsValid_BaseSchemaNoTraits(HttpRunner):
    """OP#13 - Traits: base has no traits-schema.

    Derived has no traits - passes.
    """
    config = Config("OP#13 - No Traits At All").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.notr.event.v1~",
            {
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base without traits-schema",
        ),
        _register_derived(
            "gts://gts.x.test13.notr.event.v1~x.test13._.plain.v1~",
            "gts://gts.x.test13.notr.event.v1~",
            {
                "type": "object",
                "properties": {
                    "extra": {"type": "string"},
                },
            },
            "register derived without traits",
        ),
        _validate_type_schema(
            "gts.x.test13.notr.event.v1~x.test13._.plain.v1~",
            True,
            "validate - no traits to check, should pass",
        ),
    ]


class TestCaseOp13_TraitsInvalid_MinimumViolation(HttpRunner):
    """OP#13 - Traits: integer trait violates minimum constraint - fails"""
    config = Config("OP#13 - Trait Minimum Violation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.minv.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "maxRetries": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 10,
                            "default": 3,
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with integer trait with min/max",
        ),
        _register_derived(
            "gts://gts.x.test13.minv.event.v1~x.test13._.neg_retry.v1~",
            "gts://gts.x.test13.minv.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "maxRetries": -1,
                },
            },
            "register derived with negative maxRetries",
        ),
        _validate_type_schema(
            "gts.x.test13.minv.event.v1~x.test13._.neg_retry.v1~",
            False,
            "validate should fail - maxRetries below minimum",
        ),
    ]


class TestCaseOp13_TraitsValid_RefBasedTraitSchema(HttpRunner):
    """OP#13 - Traits: base uses $ref to standalone reusable trait schemas"""
    config = Config(
        "OP#13 - Ref-Based Trait Schema"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register standalone reusable trait schema: RetentionTrait
        _register(
            "gts://gts.x.test13.traits.retention.v1~",
            {
                "type": "object",
                "properties": {
                    "retention": {
                        "description": "ISO 8601 retention duration.",
                        "type": "string",
                        "default": "P30D",
                    },
                },
            },
            "register standalone RetentionTrait schema",
        ),
        # Register standalone reusable trait schema: TopicTrait
        _register(
            "gts://gts.x.test13.traits.topic.v1~",
            {
                "type": "object",
                "properties": {
                    "topicRef": {
                        "description": "Topic reference.",
                        "type": "string",
                        "x-gts-ref": "gts.x.test13.events.topic.v1~",
                    },
                },
            },
            "register standalone TopicTrait schema",
        ),
        # Register base that composes traits via $ref + allOf
        _register(
            "gts://gts.x.test13.ref.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "allOf": [
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".traits.retention.v1~"
                            ),
                        },
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".traits.topic.v1~"
                            ),
                        },
                    ],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with $ref trait schemas",
        ),
        # Derived provides all trait values
        _register_derived(
            (
                "gts://gts.x.test13.ref.event.v1~"
                "x.test13._.ref_leaf.v1~"
            ),
            "gts://gts.x.test13.ref.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                    "retention": "P90D",
                },
            },
            "register derived resolving $ref traits",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.ref.event.v1~"
                "x.test13._.ref_leaf.v1~"
            ),
            True,
            "validate - $ref traits resolved",
        ),
    ]


class TestCaseOp13_TraitsInvalid_RefBasedMissingTrait(HttpRunner):
    """OP#13 - Traits: $ref trait schema, derived missing required trait"""
    config = Config(
        "OP#13 - Ref-Based Missing Trait"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.refm_traits.retention.v1~",
            {
                "type": "object",
                "properties": {
                    "retention": {
                        "description": (
                            "ISO 8601 retention duration."
                        ),
                        "type": "string",
                        "default": "P30D",
                    },
                },
            },
            "register standalone RetentionTrait schema",
        ),
        _register(
            "gts://gts.x.test13.refm_traits.topic.v1~",
            {
                "type": "object",
                "properties": {
                    "topicRef": {
                        "description": "Topic reference.",
                        "type": "string",
                        "x-gts-ref": (
                            "gts.x.test13.events.topic.v1~"
                        ),
                    },
                },
                "required": ["topicRef"],
            },
            "register standalone TopicTrait schema",
        ),
        _register(
            "gts://gts.x.test13.refm_missing.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "allOf": [
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".refm_traits.retention.v1~"
                            ),
                        },
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".refm_traits.topic.v1~"
                            ),
                        },
                    ],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with $ref trait schemas",
        ),
        # Derived only provides retention, missing topicRef
        _register_derived(
            (
                "gts://gts.x.test13.refm_missing.event.v1~"
                "x.test13._.ref_incomplete.v1~"
            ),
            "gts://gts.x.test13.refm_missing.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P90D",
                },
            },
            "register derived missing topicRef from $ref trait",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.refm_missing.event.v1~"
                "x.test13._.ref_incomplete.v1~"
            ),
            False,
            "validate should fail - topicRef not resolved",
        ),
    ]


class TestCaseOp13_TraitsValid_NarrowingInDerived(HttpRunner):
    """OP#13 - Traits: derived narrows trait schema (adds constraints)"""
    config = Config(
        "OP#13 - Trait Schema Narrowing"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.narrow.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "description": "Processing priority.",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with open priority trait",
        ),
        # Mid-level narrows priority to enum
        _register_derived(
            (
                "gts://gts.x.test13.narrow.event.v1~"
                "x.test13._.mid_narrow.v1~"
            ),
            "gts://gts.x.test13.narrow.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "enum": [
                                "low", "medium",
                                "high", "critical",
                            ],
                        },
                    },
                },
                "x-gts-traits": {
                    "priority": "high",
                },
            },
            "register mid-level narrowing priority to enum",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.narrow.event.v1~"
                "x.test13._.mid_narrow.v1~"
            ),
            True,
            "validate - narrowed trait with valid value",
        ),
        # Leaf provides value within narrowed enum
        _register_derived(
            (
                "gts://gts.x.test13.narrow.event.v1~"
                "x.test13._.mid_narrow.v1~"
                "x.test13._.leaf_narrow.v1~"
            ),
            (
                "gts://gts.x.test13.narrow.event.v1~"
                "x.test13._.mid_narrow.v1~"
            ),
            {
                "type": "object",
                "x-gts-traits": {
                    "priority": "critical",
                },
            },
            "register leaf with valid narrowed priority",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.narrow.event.v1~"
                "x.test13._.mid_narrow.v1~"
                "x.test13._.leaf_narrow.v1~"
            ),
            True,
            "validate leaf - priority within narrowed enum",
        ),
    ]


class TestCaseOp13_TraitsInvalid_NarrowingViolation(HttpRunner):
    """OP#13 - Traits: leaf value violates narrowed enum from mid-level"""
    config = Config(
        "OP#13 - Narrowing Violation"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.nv.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.nv.event.v1~"
                "x.test13._.mid_nv.v1~"
            ),
            "gts://gts.x.test13.nv.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "enum": [
                                "low", "medium",
                                "high", "critical",
                            ],
                        },
                    },
                },
                "x-gts-traits": {
                    "priority": "high",
                },
            },
            "register mid-level narrowing priority",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.nv.event.v1~"
                "x.test13._.mid_nv.v1~"
                "x.test13._.leaf_bad_nv.v1~"
            ),
            (
                "gts://gts.x.test13.nv.event.v1~"
                "x.test13._.mid_nv.v1~"
            ),
            {
                "type": "object",
                "x-gts-traits": {
                    "priority": "ultra_high",
                },
            },
            "register leaf with value outside narrowed enum",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.nv.event.v1~"
                "x.test13._.mid_nv.v1~"
                "x.test13._.leaf_bad_nv.v1~"
            ),
            False,
            "validate should fail - priority not in enum",
        ),
    ]


class TestCaseOp13_TraitsValid_DefaultsFromRefSchema(HttpRunner):
    """OP#13 - Traits: defaults from $ref trait schema fill values"""
    config = Config(
        "OP#13 - Defaults From Ref Schema"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Use the standalone RetentionTrait (default P30D)
        # and TopicTrait (no default) registered earlier
        _register(
            "gts://gts.x.test13.refd.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "allOf": [
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".traits.retention.v1~"
                            ),
                        },
                    ],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with $ref retention trait only",
        ),
        # Derived provides no traits - retention default fills
        _register_derived(
            (
                "gts://gts.x.test13.refd.event.v1~"
                "x.test13._.default_ref.v1~"
            ),
            "gts://gts.x.test13.refd.event.v1~",
            {
                "type": "object",
            },
            "register derived with no traits (rely on $ref default)",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.refd.event.v1~"
                "x.test13._.default_ref.v1~"
            ),
            True,
            "validate - retention default from $ref schema fills",
        ),
    ]


class TestCaseOp13_TraitsInvalid_APBlocksExtension(HttpRunner):
    """OP#13 - Traits: ancestor additionalProperties=false blocks new fields.

    Under ADR-0002 chain aggregation, the effective trait-schema is allOf of
    all ancestor declarations. The ancestor's additionalProperties:false is
    carried into the aggregated allOf and rejects the descendant's new field.
    """
    config = Config(
        "OP#13 - Traits additionalProperties Blocks Extension"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.ap.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "retention": {"type": "string"},
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with traits-schema additionalProperties=false",
        ),
        _register_derived(
            "gts://gts.x.test13.ap.event.v1~x.test13._.ap_mid.v1~",
            "gts://gts.x.test13.ap.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                        },
                    },
                },
                "x-gts-traits": {
                    "retention": "P30D",
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                },
            },
            "register mid-level that extends trait schema with topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.ap.event.v1~x.test13._.ap_mid.v1~",
            False,
            (
                "validate should fail - base additionalProperties=false "
                "blocks topicRef"
            ),
        ),
    ]


class TestCaseOp13_TraitsInvalid_AbstractAPBlocksSchemaExtensionNoValues(HttpRunner):
    """OP#13 - Traits: abstract descendant cannot extend a closed trait schema.

    The failure must be based on descendant trait-schema compatibility, not on
    validating provided x-gts-traits values: this abstract descendant provides
    no trait values and skips completeness, but its new topicRef property is
    still rejected by the ancestor's additionalProperties:false branch.
    """

    config = Config(
        "OP#13 - Abstract traits schema extension blocked by AP false"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.apabs.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "retention": {"type": "string"},
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with closed traits-schema",
        ),
        _register_derived(
            "gts://gts.x.test13.apabs.event.v1~x.test13._.ap_child.v1~",
            "gts://gts.x.test13.apabs.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.events.topic.v1~",
                        },
                    },
                },
            },
            "register abstract child extending closed trait schema",
            top_level={"x-gts-abstract": True},
        ),
        _validate_type_schema(
            "gts.x.test13.apabs.event.v1~x.test13._.ap_child.v1~",
            False,
            "validate should fail - abstract child trait schema is incompatible",
        ),
    ]


class TestCaseOp13_TraitsInvalid_DerivedHasTraitsButNoTraitSchema(HttpRunner):
    """OP#13 - Traits: derived provides x-gts-traits.

    No x-gts-traits-schema exists.
    """
    config = Config(
        "OP#13 - Derived Traits Without Trait Schema"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.nt0.event.v1~",
            {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base without traits-schema",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.nt0.event.v1~"
                "x.test13._.derived_has_traits.v1~"
            ),
            "gts://gts.x.test13.nt0.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D"},
            },
            "register derived with x-gts-traits but no traits-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.nt0.event.v1~x.test13._.derived_has_traits.v1~",
            False,
            "validate should fail - trait values have no trait schema",
        ),
    ]


class TestCaseOp13_TraitsInvalid_BaseHasTraitsButNoTraitSchema(HttpRunner):
    """OP#13 - Traits: base provides x-gts-traits.

    No x-gts-traits-schema exists.
    """
    config = Config(
        "OP#13 - Base Traits Without Trait Schema"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.nt1.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with x-gts-traits but no traits-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.nt1.event.v1~",
            False,
            "validate should fail - x-gts-traits without x-gts-traits-schema",
        ),
    ]


class TestCaseOp13_TraitsInvalid_ConstNarrowingViolationInLeaf(HttpRunner):
    """OP#13 - Traits: mid-level narrows retention to const.

    Leaf tries different value.
    """
    config = Config(
        "OP#13 - Const Narrowing Violation"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.const.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"retention": {"type": "string"}},
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with retention trait",
        ),
        _register_derived(
            "gts://gts.x.test13.const.event.v1~x.test13._.mid_const.v1~",
            "gts://gts.x.test13.const.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"const": "P30D"}},
                },
                "x-gts-traits": {"retention": "P30D"},
            },
            "register mid-level narrowing retention to const P30D",
        ),
        _validate_type_schema(
            "gts.x.test13.const.event.v1~x.test13._.mid_const.v1~",
            True,
            "validate mid-level - const narrowing",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.const.event.v1~"
                "x.test13._.mid_const.v1~"
                "x.test13._.leaf_bad_const.v1~"
            ),
            "gts://gts.x.test13.const.event.v1~x.test13._.mid_const.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P90D"},
            },
            "register leaf overriding retention to P90D",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.const.event.v1~"
                "x.test13._.mid_const.v1~"
                "x.test13._.leaf_bad_const.v1~"
            ),
            False,
            "validate should fail - leaf violates const retention=P30D",
        ),
    ]


class TestCaseOp13_TraitsValid_ConstNarrowingLeafMatches(HttpRunner):
    """OP#13 - Traits: mid-level narrows retention to const.

    Leaf provides same value.
    """
    config = Config(
        "OP#13 - Const Narrowing Leaf Match"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.constm.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"retention": {"type": "string"}},
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with retention trait",
        ),
        _register_derived(
            "gts://gts.x.test13.constm.event.v1~x.test13._.mid_constm.v1~",
            "gts://gts.x.test13.constm.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"const": "P30D"}},
                },
                "x-gts-traits": {"retention": "P30D"},
            },
            "register mid-level narrowing retention to const P30D",
        ),
        _validate_type_schema(
            "gts.x.test13.constm.event.v1~x.test13._.mid_constm.v1~",
            True,
            "validate mid-level - const narrowing",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.constm.event.v1~"
                "x.test13._.mid_constm.v1~"
                "x.test13._.leaf_ok_constm.v1~"
            ),
            "gts://gts.x.test13.constm.event.v1~x.test13._.mid_constm.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D"},
            },
            "register leaf with retention matching const P30D",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.constm.event.v1~"
                "x.test13._.mid_constm.v1~"
                "x.test13._.leaf_ok_constm.v1~"
            ),
            True,
            "validate leaf - retention matches const",
        ),
    ]


class TestCaseOp13_TraitsInvalid_CyclingRef_SelfRef(HttpRunner):
    """OP#13 - Traits: trait-schema body $refs itself — true self-cycle.

    Under v0.12 ADR-0002, multiple independent occurrences of the same $ref
    in an allOf are allowed (redundant manual aggregation). What MUST still
    fail is a TRUE cycle where a trait-schema's body references its own ID,
    causing infinite resolution. This case sets up exactly that.
    """
    config = Config(
        "OP#13 - Traits Self-Referencing Ref"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.cyc.selfref.v1~",
            {
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test13"
                            ".cyc.selfref.v1~"
                        ),
                    },
                ],
                "properties": {
                    "retention": {
                        "type": "string",
                    },
                },
            },
            "register trait schema that $refs itself",
        ),
        _register(
            "gts://gts.x.test13.cyc.selfevt.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "$$ref": (
                        "gts://gts.x.test13"
                        ".cyc.selfref.v1~"
                    ),
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base referencing self-cycling trait schema",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.cyc.selfevt.v1~"
                "x.test13._.cyc_self_leaf.v1~"
            ),
            "gts://gts.x.test13.cyc.selfevt.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P30D",
                },
            },
            "register derived with traits",
        ),
        _validate_type_schema(
            "gts.x.test13.cyc.selfref.v1~",
            True,
            "validate standalone recursive trait schema",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.cyc.selfevt.v1~"
                "x.test13._.cyc_self_leaf.v1~"
            ),
            False,
            "validate should fail - true self-cycle in trait-schema chain",
        ),
    ]


class TestCaseOp13_TraitsInvalid_CyclingRef_TwoNode(HttpRunner):
    """OP#13 - Traits: trait schema A refs B, B refs A."""
    config = Config(
        "OP#13 - Traits Two-Node Ref Cycle"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.cyc2.trait_a.v1~",
            {
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test13"
                            ".cyc2.trait_b.v1~"
                        ),
                    },
                ],
                "properties": {
                    "retention": {"type": "string"},
                },
            },
            "register trait schema A referencing B",
        ),
        _register(
            "gts://gts.x.test13.cyc2.trait_b.v1~",
            {
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test13"
                            ".cyc2.trait_a.v1~"
                        ),
                    },
                ],
                "properties": {
                    "topicRef": {
                        "type": "string",
                        "x-gts-ref": (
                            "gts.x.test13.events.topic.v1~"
                        ),
                    },
                },
            },
            "register trait schema B referencing A",
        ),
        _register(
            "gts://gts.x.test13.cyc2.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "allOf": [
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".cyc2.trait_a.v1~"
                            ),
                        },
                    ],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with cycling trait refs",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.cyc2.event.v1~"
                "x.test13._.cyc2_leaf.v1~"
            ),
            "gts://gts.x.test13.cyc2.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P30D",
                    "topicRef": (
                        "gts.x.test13.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                },
            },
            "register derived with traits",
        ),
        _validate_type_schema(
            "gts.x.test13.cyc2.trait_a.v1~",
            True,
            "validate standalone recursive trait schema A",
        ),
        _validate_type_schema(
            "gts.x.test13.cyc2.trait_b.v1~",
            True,
            "validate standalone recursive trait schema B",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.cyc2.event.v1~"
                "x.test13._.cyc2_leaf.v1~"
            ),
            False,
            "validate should fail - two-node cycle in trait refs",
        ),
    ]

# NOTE (v0.12): TestCaseOp13_TraitsInvalid_TraitsSchemaNotObject was removed.
# Under ADR-0002 the value space for x-gts-traits-schema is "subschema OR true
# OR false"; an object subschema with type=integer is admissible *syntactically*.
# Trait-value violations against such a schema are covered by
# TestCaseOp13_TraitsValueViolatesIntegerSchema below.



# ---------------------------------------------------------------------------
# ADR-0002: x-gts-traits-schema as a JSON Schema subschema
#
# Value MAY be an object subschema, boolean true, or boolean false. The
# effective trait-schema at any type is the allOf of all declarations along
# the $id chain. Descendants need not repeat ancestor declarations, but if
# they declare a trait-schema it must be compatible with the chain.
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitsSchema_DescendantOmitsAncestorDecl_AggregatedViaAllOf(HttpRunner):
    """ADR-0002: descendant omits x-gts-traits-schema; effective is aggregated.

    Base declares the trait-schema; derived declares no x-gts-traits-schema
    of its own but supplies a value. The registry composes ancestor
    declarations via allOf; the value satisfies the aggregated schema.
    """

    config = Config("OP#13 ADR-0002: descendant omits trait-schema decl").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggomit.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "retention": {"type": "string", "default": "P30D"},
                    },
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register valid base with trait-schema default",
        ),
        _register_derived(
            "gts://gts.x.test13.aggomit.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggomit.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P90D"},
            },
            "register derived - no trait-schema decl, supplies value only",
        ),
        _validate_type_schema(
            "gts.x.test13.aggomit.event.v1~x.test13._.kid.v1~",
            True,
            "validate derived - aggregated trait-schema satisfied",
        ),
    ]


class TestCaseOp13_TraitsSchema_DescendantAddsNewField(HttpRunner):
    """ADR-0002: descendant adds a new trait field; aggregated via allOf.

    Base declares `retention` with a default. Descendant declares only
    `supportLevel` (without restating retention). Both types are independently
    valid, and the descendant satisfies the aggregated effective trait-schema.
    """

    config = Config("OP#13 ADR-0002: descendant adds new trait field").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggadd.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string", "default": "P30D"},
                    },
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register valid base with default retention",
        ),
        _register_derived(
            "gts://gts.x.test13.aggadd.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggadd.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "supportLevel": {"type": "string"},
                    },
                    "required": ["supportLevel"],
                },
                "x-gts-traits": {
                    "retention": "P30D",
                    "supportLevel": "premium",
                },
            },
            "register derived adding supportLevel only",
        ),
        _validate_type_schema(
            "gts.x.test13.aggadd.event.v1~",
            True,
            "validate base - default resolves retention",
        ),
        _validate_type_schema(
            "gts.x.test13.aggadd.event.v1~x.test13._.kid.v1~",
            True,
            "validate derived - valid base and aggregated traits",
        ),
    ]


class TestCaseOp13_TraitsSchema_DescendantCannotAddFieldToClosedBase(HttpRunner):
    """An ancestor's closed trait schema rejects descendant fields.

    The base is independently valid because its required retention trait has a
    default. Its `additionalProperties: false` branch remains part of the
    effective allOf and rejects the descendant's new `supportLevel` property.
    """

    config = Config("OP#13 ADR-0002: closed base blocks new trait field").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggaddclosed.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "retention": {"type": "string", "default": "P30D"},
                    },
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register valid closed base with default retention",
        ),
        _register_derived(
            "gts://gts.x.test13.aggaddclosed.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggaddclosed.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "supportLevel": {"type": "string"},
                    },
                    "required": ["supportLevel"],
                },
                "x-gts-traits": {
                    "retention": "P30D",
                    "supportLevel": "premium",
                },
            },
            "register derived adding supportLevel to closed base",
        ),
        _validate_type_schema(
            "gts.x.test13.aggaddclosed.event.v1~",
            True,
            "validate closed base - default resolves retention",
        ),
        _validate_type_schema(
            "gts.x.test13.aggaddclosed.event.v1~x.test13._.kid.v1~",
            False,
            "validate derived - closed base rejects supportLevel",
        ),
    ]


class TestCaseOp13_TraitsSchema_DescendantOfInvalidBaseFails(HttpRunner):
    """A derived type is invalid when an ancestor type is invalid.

    The derived type supplies all values required by its own effective trait
    schema, but its non-abstract base has an unresolved required trait. Explicit
    validation is transitive, so both the base and derived type fail.
    """

    config = Config("OP#13: descendant of invalid base fails").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggaddbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string"},
                    },
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register invalid base with unresolved retention",
        ),
        _register_derived(
            "gts://gts.x.test13.aggaddbad.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggaddbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "supportLevel": {"type": "string"},
                    },
                    "required": ["supportLevel"],
                },
                "x-gts-traits": {
                    "retention": "P30D",
                    "supportLevel": "premium",
                },
            },
            "register locally complete derived type over invalid base",
        ),
        _validate_type_schema(
            "gts.x.test13.aggaddbad.event.v1~",
            False,
            "validate base - required retention is unresolved",
        ),
        _validate_type_schema(
            "gts.x.test13.aggaddbad.event.v1~x.test13._.kid.v1~",
            False,
            "validate derived - ancestor base is invalid",
        ),
        _register_instance(
            {
                "id": (
                    "gts.x.test13.aggaddbad.event.v1~"
                    "x.test13._.kid.v1~x.test13._.example.v1"
                ),
            },
            "register structurally valid instance of invalid derived type",
        ),
        _validate_instance(
            (
                "gts.x.test13.aggaddbad.event.v1~"
                "x.test13._.kid.v1~x.test13._.example.v1"
            ),
            False,
            "validate well-known instance - its type dependency is invalid",
        ),
        _register_instance(
            {
                "id": "123e4567-e89b-42d3-a456-426614174000",
                "type": "gts.x.test13.aggaddbad.event.v1~x.test13._.kid.v1~",
            },
            "register anonymous instance of invalid derived type",
        ),
        _validate_instance(
            "123e4567-e89b-42d3-a456-426614174000",
            False,
            "validate anonymous instance - its type dependency is invalid",
        ),
    ]


class TestCaseOp13_TraitsSchema_BooleanTrue_AnyTraitsAllowed(HttpRunner):
    """ADR-0002: x-gts-traits-schema: true permits arbitrary traits.

    Subschema `true` accepts any value; descendant may carry any
    x-gts-traits object.
    """

    config = Config("OP#13 ADR-0002: trait-schema true permits any traits").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggtrue.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": True,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with trait-schema: true",
        ),
        _register_derived(
            "gts://gts.x.test13.aggtrue.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggtrue.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P30D",
                    "topic": "events",
                    "anything": 42,
                },
            },
            "register derived with arbitrary traits",
        ),
        _validate_type_schema(
            "gts.x.test13.aggtrue.event.v1~x.test13._.kid.v1~",
            True,
            "validate derived - any traits allowed under true",
        ),
    ]


class TestCaseOp13_TraitsSchema_BooleanFalse_NoTraits_Ok(HttpRunner):
    """ADR-0002: x-gts-traits-schema: false prohibits traits, not descendants.

    A concrete descendant with no x-gts-traits MUST register and validate.
    `false` rules out traits, not the existence of typed descendants.
    """

    config = Config("OP#13 ADR-0002: trait-schema false + no traits passes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggfalse.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": False,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with trait-schema: false",
        ),
        _register_derived(
            "gts://gts.x.test13.aggfalse.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggfalse.event.v1~",
            {"type": "object"},
            "register derived - no x-gts-traits",
        ),
        _validate_type_schema(
            "gts.x.test13.aggfalse.event.v1~x.test13._.kid.v1~",
            True,
            "validate derived - no traits, false-schema not exercised",
        ),
    ]


class TestCaseOp13_TraitsSchema_BooleanFalse_DescendantSetsTraits_Fails(HttpRunner):
    """ADR-0002: descendant tries to set x-gts-traits against a false-schema.

    Aggregated effective schema is `false`; any traits object fails validation.
    """

    config = Config("OP#13 ADR-0002: trait-schema false rejects traits").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggfalsetr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": False,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with trait-schema: false",
        ),
        _register_derived(
            "gts://gts.x.test13.aggfalsetr.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggfalsetr.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D"},
            },
            "register derived with traits against false-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.aggfalsetr.event.v1~x.test13._.kid.v1~",
            False,
            "validate derived - traits rejected by false-schema",
        ),
    ]


class TestCaseOp13_TraitsSchema_BooleanFalse_Inherits_DescendantSetsTraits_Fails(HttpRunner):
    """ADR-0002: false anywhere in the chain makes effective schema unsatisfiable.

    Base is false; mid declares an object trait-schema; leaf supplies traits.
    allOf(false, {...}) is false; leaf's traits cannot validate.
    """

    config = Config("OP#13 ADR-0002: false inherited blocks traits").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggfalsei.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": False,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with trait-schema: false",
        ),
        _register_derived(
            "gts://gts.x.test13.aggfalsei.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.aggfalsei.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                },
            },
            "register mid declaring object trait-schema",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.aggfalsei.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.aggfalsei.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D"},
            },
            "register leaf supplying traits",
        ),
        _validate_type_schema(
            "gts.x.test13.aggfalsei.event.v1~",
            True,
            "validate base - false trait-schema permits no trait values",
        ),
        _validate_type_schema(
            "gts.x.test13.aggfalsei.event.v1~x.test13._.mid.v1~",
            False,
            "validate mid - false trait-schema permits no traits in derived types",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.aggfalsei.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            False,
            "validate leaf - allOf(false, {...}) = false",
        ),
    ]


class TestCaseOp13_TraitsSchema_IncompatibleDescendantSchema_Fails(HttpRunner):
    """ADR-0002: descendant's own trait-schema must be compatible with ancestor.

    Parent declares retention.minLength=5; descendant declares
    retention.maxLength=3. Aggregated allOf is unsatisfiable on `retention`
    — a non-abstract descendant with `retention` required cannot satisfy
    completeness with any value.
    """

    config = Config("OP#13 ADR-0002: incompatible descendant trait-schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggincomp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string", "minLength": 5},
                    },
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with minLength=5",
        ),
        _register_derived(
            "gts://gts.x.test13.aggincomp.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggincomp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string", "maxLength": 3},
                    },
                },
                "x-gts-traits": {"retention": "P30D"},
            },
            "register derived with incompatible maxLength=3",
        ),
        _validate_type_schema(
            "gts.x.test13.aggincomp.event.v1~x.test13._.kid.v1~",
            False,
            "validate derived - aggregated allOf is unsatisfiable",
        ),
    ]


class TestCaseOp13_TraitsSchema_AbstractIncompatibleNoValues_Fails(HttpRunner):
    """ADR-0002: abstract descendant trait-schema must still narrow ancestor.

    The abstract child provides no x-gts-traits values, so ordinary value
    validation has nothing concrete to reject. Validation must still fail
    because retention changes from string to integer in the descendant
    x-gts-traits-schema, which is not a narrowing of the ancestor trait.
    """

    config = Config(
        "OP#13 ADR-0002: abstract incompatible trait-schema without values"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.abstincomp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string"},
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with retention string trait",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.abstincomp.event.v1~"
                "x.test13._.child.v1~"
            ),
            "gts://gts.x.test13.abstincomp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "integer"},
                    },
                },
            },
            "register abstract child changing retention trait type",
            top_level={"x-gts-abstract": True},
        ),
        _validate_type_schema(
            "gts.x.test13.abstincomp.event.v1~",
            True,
            "validate should pass - no completeness check",
        ),
        _validate_type_schema(
            "gts.x.test13.abstincomp.event.v1~x.test13._.child.v1~",
            False,
            "validate should fail - abstract child trait schema changes type",
        ),
    ]


class TestCaseOp13_TraitsSchema_AbstractClosedDescendantOrphansAncestor_Fails(
    HttpRunner
):
    """ADR-0002: a closed descendant trait-schema must not orphan an ancestor trait.

    The effective trait-schema composes ancestor and descendant contributions as
    sibling allOf branches, and additionalProperties is scoped to its own branch.
    The abstract child sets additionalProperties:false but does not restate the
    ancestor's retention trait, so retention becomes unusable (any value for it
    is rejected by the child branch). The child provides no values, so this is
    caught by descendant trait-schema compatibility, not value validation.
    """

    config = Config(
        "OP#13 ADR-0002: closed descendant orphans ancestor trait"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.abstorphan.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string"},
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with retention string trait",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.abstorphan.event.v1~"
                "x.test13._.child.v1~"
            ),
            "gts://gts.x.test13.abstorphan.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "topicRef": {"type": "string"},
                    },
                },
            },
            "register abstract child closing surface without restating retention",
            top_level={"x-gts-abstract": True},
        ),
        _validate_type_schema(
            "gts.x.test13.abstorphan.event.v1~x.test13._.child.v1~",
            False,
            "validate should fail - closed child orphans ancestor retention trait",
        ),
    ]


class TestCaseOp13_TraitsSchema_AbstractNestedClosedDescendantOrphansAncestor_Fails(
    HttpRunner
):
    """ADR-0002: closed nested descendant trait-schema must not orphan ancestors.

    The child keeps the top-level routing trait but closes the nested routing
    object without restating the ancestor's routing.source field. Under allOf,
    any routing.source value is rejected by the child branch, so validation
    must fail even though the abstract child provides no trait values.
    """

    config = Config(
        "OP#13 ADR-0002: closed nested descendant orphans ancestor trait"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.abstnestedorphan.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with nested routing.source trait",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.abstnestedorphan.event.v1~"
                "x.test13._.child.v1~"
            ),
            "gts://gts.x.test13.abstnestedorphan.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "target": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "register abstract child closing routing without source",
            top_level={"x-gts-abstract": True},
        ),
        _validate_type_schema(
            "gts.x.test13.abstnestedorphan.event.v1~x.test13._.child.v1~",
            False,
            "validate should fail - closed nested child orphans routing.source",
        ),
    ]


class TestCaseOp13_TraitsSchema_AbstractNestedClosedDescendantRestatesAncestor_Ok(
    HttpRunner
):
    """ADR-0002: closed nested descendant may restate ancestor nested traits."""

    config = Config(
        "OP#13 ADR-0002: closed nested descendant restates ancestor trait"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.abstnestedrestate.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with nested routing.source trait",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.abstnestedrestate.event.v1~"
                "x.test13._.child.v1~"
            ),
            "gts://gts.x.test13.abstnestedrestate.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "register abstract child closing routing and restating source",
            top_level={"x-gts-abstract": True},
        ),
        _validate_type_schema(
            "gts.x.test13.abstnestedrestate.event.v1~x.test13._.child.v1~",
            True,
            "validate should pass - closed nested child restates routing.source",
        ),
    ]


class TestCaseOp13_TraitsSchema_AbstractValidNarrowingNoValues_Ok(HttpRunner):
    """ADR-0002: a valid narrowing descendant trait-schema must pass.

    Positive guard against over-rejection: the abstract child narrows the
    ancestor priority trait (open string -> enum subset) and adds an optional
    trait under an open ancestor, providing no values. Descendant trait-schema
    compatibility must accept this.
    """

    config = Config(
        "OP#13 ADR-0002: abstract valid narrowing trait-schema without values"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.abstnarrow.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "string"},
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with open priority trait",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.abstnarrow.event.v1~"
                "x.test13._.child.v1~"
            ),
            "gts://gts.x.test13.abstnarrow.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "enum": ["low", "high"],
                        },
                        "note": {"type": "string"},
                    },
                },
            },
            "register abstract child narrowing priority and adding optional note",
            top_level={"x-gts-abstract": True},
        ),
        _validate_type_schema(
            "gts.x.test13.abstnarrow.event.v1~x.test13._.child.v1~",
            True,
            "validate should pass - child narrows priority and adds optional trait",
        ),
    ]


class TestCaseOp13_TraitsSchema_RedundantAncestorRefAllowed(HttpRunner):
    """ADR-0002 §"Patterns within Option 2A": redundant ancestor-ref is allowed.

    Trait-schema lives at a standalone GTS type and is referenced from the
    base's x-gts-traits-schema. The descendant explicitly composes its own
    trait-schema as allOf:[{$ref: ancestor-trait-schema-type}, {delta}].
    Under chain-aggregation this manual composition is redundant (the chain
    already aggregates via allOf), but not invalid per the extension framing
    (any syntactically valid JSON Schema is a valid GTS Type Schema; ADR-0001).
    """

    config = Config("OP#13 ADR-0002: redundant ancestor ref allowed").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggrr.trschema.v1~",
            {
                "type": "object",
                "properties": {"retention": {"type": "string"}},
                "required": ["retention"],
            },
            "register standalone ancestor trait-schema type",
        ),
        _register_abstract(
            "gts://gts.x.test13.aggrr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "$$ref": "gts://gts.x.test13.aggrr.trschema.v1~",
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base referencing the standalone trait-schema",
        ),
        _register_derived(
            "gts://gts.x.test13.aggrr.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.aggrr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "allOf": [
                        {"$$ref": "gts://gts.x.test13.aggrr.trschema.v1~"},
                        {"type": "object", "properties": {"supportLevel": {"type": "string"}}},
                    ],
                },
                "x-gts-traits": {"retention": "P30D", "supportLevel": "premium"},
            },
            "register derived with explicit redundant ancestor-ref in trait-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.aggrr.event.v1~x.test13._.kid.v1~",
            True,
            "validate derived - redundant ref is allowed",
        ),
    ]


class TestCaseOp13_TraitsSchema_ObjectFormStillValid(HttpRunner):
    """ADR-0002 regression: pre-v0.12 object form remains valid.

    Ensures the dominant historical form (x-gts-traits-schema as an object)
    is unchanged by the v0.12 subschema framing that admits booleans
    (ADR-0002).
    """

    config = Config("OP#13 ADR-0002: object form still valid").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggobjform.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "retention": {"type": "string", "default": "P30D"},
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with classic object trait-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.aggobjform.event.v1~",
            True,
            "validate base - object form still valid",
        ),
    ]


class TestCaseOp13_TraitsSchema_StandaloneRefPattern_3Level(HttpRunner):
    """ADR-0002: standalone $ref'd trait-schema + 3-level chain aggregation.

    Trait-schema lives at a standalone $id and is $ref'd by the host's
    x-gts-traits-schema. Mid level adds another trait-schema declaration
    that aggregates via allOf. Leaf supplies values for both layers.
    """

    config = Config("OP#13 ADR-0002: standalone ref-pattern + 3-level chain").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.aggrp.tschema.v1~",
            {
                "type": "object",
                "properties": {"retention": {"type": "string"}},
                "required": ["retention"],
            },
            "register standalone trait-schema type",
        ),
        _register_abstract(
            "gts://gts.x.test13.aggrp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "$$ref": "gts://gts.x.test13.aggrp.tschema.v1~",
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with $ref'd trait-schema",
        ),
        _register_derived(
            "gts://gts.x.test13.aggrp.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.aggrp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"supportLevel": {"type": "string"}},
                    "required": ["supportLevel"],
                },
            },
            "register abstract mid adding supportLevel inline",
            top_level={"x-gts-abstract": True},
        ),
        _register_derived(
            (
                "gts://gts.x.test13.aggrp.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.aggrp.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D", "supportLevel": "gold"},
            },
            "register leaf supplying both traits",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.aggrp.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            True,
            "validate leaf - 3-level aggregation across ref-pattern + inline",
        ),
    ]


# ---------------------------------------------------------------------------
# ADR-0003: trait completeness keyed on x-gts-abstract
#
# Completeness is enforced (via /validate-type-schema) for non-abstract types
# only. The materialized effective traits object (defaults substituted) MUST
# satisfy the effective trait-schema. Abstract types skip the check.
# ---------------------------------------------------------------------------


class TestCaseOp13_Completeness_AbstractType_UnresolvedRequired_Succeeds(HttpRunner):
    """ADR-0003: abstract types skip completeness even with unresolved required.

    Base declares a required trait with no default and provides no value;
    base is x-gts-abstract: true; validation passes (check skipped).
    """

    config = Config("OP#13 ADR-0003: abstract skips completeness").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.compabs.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with unresolved required trait",
        ),
        _validate_type_schema(
            "gts.x.test13.compabs.event.v1~",
            True,
            "validate abstract - completeness skipped",
        ),
    ]


class TestCaseOp13_Completeness_AbstractPreservesRequiredInConstValue(HttpRunner):
    """Skipping completeness must not rewrite data stored inside const."""

    config = Config(
        "OP#13 ADR-0003: abstract preserves required key in const value"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.compabsconst.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "config": {"const": {"required": ["a"]}},
                    },
                    "required": ["unresolved"],
                },
                "x-gts-traits": {"config": {"required": ["a"]}},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract type with required key inside trait const data",
        ),
        _validate_type_schema(
            "gts.x.test13.compabsconst.event.v1~",
            True,
            "validate abstract - completeness skipped without rewriting const data",
        ),
    ]


class TestCaseOp13_Completeness_AbstractPreservesRequiredPropertySchema(HttpRunner):
    """Ignoring required must not drop a trait property with that name."""

    config = Config(
        "OP#13 ADR-0003: abstract preserves property named required"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.compabsprop.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"required": {"type": "string"}},
                    "required": ["unresolved"],
                },
                "x-gts-traits": {"required": 42},
                "properties": {"id": {"type": "string"}},
            },
            "register abstract type with invalid property named required",
        ),
        _validate_type_schema(
            "gts.x.test13.compabsprop.event.v1~",
            False,
            "reject wrong type for property named required",
        ),
    ]


class TestCaseOp13_TraitsInvalid_AbstractProvidedValueWrongType_Fails(HttpRunner):
    """Abstractness skips completeness, not validation of provided values."""

    config = Config("OP#13 ADR-0003: abstract invalid provided value fails").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.compabsval.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retentionDays": {"type": "integer"}},
                    "required": ["retentionDays"],
                },
                "x-gts-traits": {"retentionDays": "thirty"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract type with invalid provided trait value",
        ),
        _validate_type_schema(
            "gts.x.test13.compabsval.event.v1~",
            False,
            "validate abstract - provided value must satisfy trait schema",
        ),
    ]


class TestCaseOp13_Completeness_NonAbstractExplicitValue_Succeeds(HttpRunner):
    """A non-abstract type may resolve a required trait explicitly."""

    config = Config("OP#13 ADR-0003: explicit value satisfies required").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.compval.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register non-abstract type with explicit required trait",
        ),
        _validate_type_schema(
            "gts.x.test13.compval.event.v1~",
            True,
            "validate non-abstract - explicit value resolves retention",
        ),
    ]


class TestCaseOp13_Completeness_NonAbstractUnresolvedRequired_Fails(HttpRunner):
    """A non-abstract type must resolve every required trait."""

    config = Config("OP#13 ADR-0003: non-abstract unresolved required fails").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.compmiss.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register non-abstract type with unresolved required trait",
        ),
        _validate_type_schema(
            "gts.x.test13.compmiss.event.v1~",
            False,
            "validate non-abstract - retention has no value or default",
        ),
    ]


class TestCaseOp13_Completeness_NonAbstractIntermediate_UnresolvedRequired_Fails(HttpRunner):
    """ADR-0003: completeness applies to every non-abstract type, not just leaves.

    Three-level chain A→B→C. B is non-abstract and has descendants registered
    after it. B leaves the required trait unresolved. The old leaf-based rule
    would have allowed B; the new rule fails it. Validate B and observe FAIL.
    """

    config = Config("OP#13 ADR-0003: non-abstract intermediate must be complete").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.compmid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract A (root)",
        ),
        _register_derived(
            "gts://gts.x.test13.compmid.event.v1~x.test13._.mid_b.v1~",
            "gts://gts.x.test13.compmid.event.v1~",
            {
                "type": "object",
            },
            "register non-abstract B without resolving topicRef",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.compmid.event.v1~"
                "x.test13._.mid_b.v1~x.test13._.leaf_c.v1~"
            ),
            "gts://gts.x.test13.compmid.event.v1~x.test13._.mid_b.v1~",
            {
                "type": "object",
                "x-gts-traits": {"topicRef": "events.orders"},
            },
            "register leaf C resolving the trait",
        ),
        _validate_type_schema(
            "gts.x.test13.compmid.event.v1~x.test13._.mid_b.v1~",
            False,
            "validate B - non-abstract with unresolved required trait, must fail",
        ),
    ]


class TestCaseOp13_Completeness_AbstractBase_ConcreteDescendantSatisfies(HttpRunner):
    """ADR-0003: abstract base + concrete descendant filling gaps.

    Abstract A with required trait, no default. Non-abstract B supplies value.
    A passes (skip). B passes (resolved).
    """

    config = Config("OP#13 ADR-0003: abstract base + concrete satisfies").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.compabsb.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base",
        ),
        _register_derived(
            "gts://gts.x.test13.compabsb.event.v1~x.test13._.concrete.v1~",
            "gts://gts.x.test13.compabsb.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"topicRef": "events.orders"},
            },
            "register concrete descendant resolving trait",
        ),
        _validate_type_schema(
            "gts.x.test13.compabsb.event.v1~",
            True,
            "validate abstract - skipped",
        ),
        _validate_type_schema(
            "gts.x.test13.compabsb.event.v1~x.test13._.concrete.v1~",
            True,
            "validate concrete - trait resolved",
        ),
    ]


class TestCaseOp13_Completeness_DefaultSatisfiesRequired(HttpRunner):
    """ADR-0003: materialization with default satisfies completeness.

    Required trait has a default. Non-abstract type omits x-gts-traits; the
    default fills the gap during materialization, validation passes.
    """

    config = Config("OP#13 ADR-0003: default satisfies required").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.compdfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string", "default": "P7D"},
                    },
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with default on required trait",
        ),
        _validate_type_schema(
            "gts.x.test13.compdfl.event.v1~",
            True,
            "validate non-abstract base - default materialized",
        ),
    ]


class TestCaseOp13_Completeness_NullDelete_RequiredNoDefault_Fails(HttpRunner):
    """ADR-0003/0004: null in descendant deletes ancestor's value.

    Ancestor sets the required trait; descendant writes null; no default
    available. After RFC 7396 merge the key is removed and materialization
    cannot re-apply a default. Non-abstract descendant fails completeness.
    """

    config = Config("OP#13 ADR-0003: null-delete required no default fails").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.compnreq.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
                "x-gts-traits": {"topicRef": "events.orders"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with topicRef set, no default",
        ),
        _register_derived(
            "gts://gts.x.test13.compnreq.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.compnreq.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"topicRef": None},
            },
            "register concrete descendant nulling topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.compnreq.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - required trait deleted with no default",
        ),
    ]


# ---------------------------------------------------------------------------
# ADR-0004: x-gts-traits merge strategy (RFC 7396 JSON Merge Patch)
#
# Traits merge along the $id chain root → leaf. Scalars last-win; objects
# merge recursively; arrays replace wholesale; null deletes the key, after
# which ADR-0003 materialization re-applies any default. Locking is done via
# standard JSON Schema `const` in x-gts-traits-schema; the registry does not
# carry a GTS-specific immutability rule.
# ---------------------------------------------------------------------------


class TestCaseOp13_Merge_ScalarOverride_LastWins(HttpRunner):
    """ADR-0004: descendant overrides ancestor scalar trait — last wins.

    Replaces the deleted TraitsInvalid_OverrideInChain. Under v0.12 the
    descendant value is the effective value; registration succeeds.
    """

    config = Config("OP#13 ADR-0004: scalar override last-wins").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mscalar.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with retention=P30D",
        ),
        _register_derived(
            "gts://gts.x.test13.mscalar.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mscalar.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P365D"},
            },
            "register descendant overriding to P365D",
        ),
        _validate_type_schema(
            "gts.x.test13.mscalar.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - scalar last-wins",
        ),
    ]


class TestCaseOp13_Merge_3Layer_MiddleOverridesBase_LeafOverridesMiddle(HttpRunner):
    """ADR-0004 §"Conformance test suite" (g): 3-layer chain, each overrides ancestor."""

    config = Config("OP#13 ADR-0004: 3-layer last-wins").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.m3layer.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P7D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base retention=P7D",
        ),
        _register_derived(
            "gts://gts.x.test13.m3layer.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.m3layer.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D"},
            },
            "register mid retention=P30D",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.m3layer.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.m3layer.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P365D"},
            },
            "register leaf retention=P365D",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.m3layer.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            True,
            "validate leaf - 3-layer last-wins",
        ),
    ]


class TestCaseOp13_Merge_NestedObject_RecursiveMerge(HttpRunner):
    """ADR-0004 §"Conformance test suite" (b): nested-object recursive merge.

    Base sets routing.{topic, partitionKey}; descendant overrides only `topic`.
    Effective routing retains `partitionKey` from base; the trait-schema
    requires both fields and is satisfied without the descendant restating
    partitionKey.
    """

    config = Config("OP#13 ADR-0004: nested object recursive merge").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnested.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "partitionKey": {"type": "string"},
                            },
                            "required": ["topic", "partitionKey"],
                        },
                    },
                    "required": ["routing"],
                },
                "x-gts-traits": {
                    "routing": {"topic": "events", "partitionKey": "userId"},
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with routing.{topic, partitionKey}",
        ),
        _register_derived(
            "gts://gts.x.test13.mnested.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnested.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "routing": {"topic": "orders"},
                },
            },
            "register descendant overriding only routing.topic",
        ),
        _validate_type_schema(
            "gts.x.test13.mnested.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - partitionKey preserved by recursive merge",
        ),
    ]


class TestCaseOp13_Merge_ArrayReplacesWholesale(HttpRunner):
    """ADR-0004 §"Conformance test suite" (c): arrays replace wholesale.

    Ancestor sets tags=["a","b","base"]; descendant replaces with ["new"].
    Effective is ["new"] — no element-level merging. We assert this both
    positively (replacement accepted under a permissive items schema) and
    negatively (next class) via a constraint the new array violates.
    """

    config = Config("OP#13 ADR-0004: array replaces wholesale").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.marrayrp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        },
                    },
                    "required": ["tags"],
                },
                "x-gts-traits": {"tags": ["a", "b", "base"]},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base tags=[a,b,base]",
        ),
        _register_derived(
            "gts://gts.x.test13.marrayrp.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.marrayrp.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"tags": ["new"]},
            },
            "register descendant tags=[new]",
        ),
        _validate_type_schema(
            "gts.x.test13.marrayrp.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - replacement accepted (minItems=1)",
        ),
    ]


class TestCaseOp13_Merge_ArrayReplacesWholesale_NegativeProvesNoMerge(HttpRunner):
    """ADR-0004 companion: ancestor had 3 items, descendant array of 1 must
    fail a minItems=2 constraint — proving array merge is replacement, not union.
    """

    config = Config("OP#13 ADR-0004: array replace, no merge").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.marrnomerg.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                        },
                    },
                    "required": ["tags"],
                },
                "x-gts-traits": {"tags": ["a", "b", "base"]},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base tags has 3 items, schema requires minItems=2",
        ),
        _register_derived(
            "gts://gts.x.test13.marrnomerg.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.marrnomerg.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"tags": ["only-one"]},
            },
            "register descendant tags=[only-one] (1 item)",
        ),
        _validate_type_schema(
            "gts.x.test13.marrnomerg.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - replacement violates minItems=2",
        ),
    ]


class TestCaseOp13_Merge_NullDelete_FallsBackToDefault(HttpRunner):
    """ADR-0004 §"Conformance test suite" (d): null deletes; default re-applies.

    Base sets retention=P30D; schema also declares default=P7D. Descendant
    writes null. Merged object omits retention; ADR-0003 materialization
    substitutes default=P7D; validation passes.
    """

    config = Config("OP#13 ADR-0004: null-delete falls back to default").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnulldfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string", "default": "P7D"},
                    },
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base retention=P30D, default=P7D",
        ),
        _register_derived(
            "gts://gts.x.test13.mnulldfl.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnulldfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": None},
            },
            "register descendant nulling retention",
        ),
        _validate_type_schema(
            "gts.x.test13.mnulldfl.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - default re-applied after null delete",
        ),
    ]


class TestCaseOp13_Merge_NullDelete_NoDefault_AbstractOk(HttpRunner):
    """ADR-0004 + ADR-0003: null-delete on a required-no-default trait,
    descendant is abstract → completeness skipped → passes.
    """

    config = Config("OP#13 ADR-0004: null-delete + abstract descendant ok").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnullabs.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
                "x-gts-traits": {"topicRef": "events.orders"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with topicRef set, no default",
        ),
        _register_abstract(
            "gts://gts.x.test13.mnullabs.event.v1~x.test13._.kid.v1~",
            {
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test13.mnullabs.event.v1~"},
                ],
                "x-gts-traits": {"topicRef": None},
            },
            "register abstract descendant nulling topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.mnullabs.event.v1~x.test13._.kid.v1~",
            True,
            "validate abstract descendant - completeness skipped",
        ),
    ]


class TestCaseOp13_Merge_ConstLock_DescendantOverrideFails(HttpRunner):
    """ADR-0004 §"Conformance test suite" (f): publisher locks with const.

    Trait-schema declares `indexed: { const: true }`. Base sets indexed=true.
    Descendant tries indexed=false. Merged value `false` fails JSON Schema
    validation against the aggregated trait-schema's const — standard
    mechanism, no GTS-specific rule.
    """

    config = Config("OP#13 ADR-0004: const lock rejects override").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mconstlk.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "indexed": {"type": "boolean", "const": True},
                    },
                    "required": ["indexed"],
                },
                "x-gts-traits": {"indexed": True},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with const-locked indexed=true",
        ),
        _register_derived(
            "gts://gts.x.test13.mconstlk.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mconstlk.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"indexed": False},
            },
            "register descendant trying indexed=false",
        ),
        _validate_type_schema(
            "gts.x.test13.mconstlk.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - const violated by override",
        ),
    ]


class TestCaseOp13_Merge_ConstLock_NullDeleteFails(HttpRunner):
    """ADR-0004 §"Conformance test suite" (g): null cannot delete a required lock.

    RFC 7396 removes `indexed` from the merged traits object, but the effective
    trait-schema also requires the property. The materialized object therefore
    fails OP#13 instead of bypassing the const constraint.
    """

    config = Config("OP#13 ADR-0004: const lock rejects null delete").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mconstdel.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "indexed": {"type": "boolean", "const": True},
                    },
                    "required": ["indexed"],
                },
                "x-gts-traits": {"indexed": True},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with const-and-required locked indexed=true",
        ),
        _register_derived(
            "gts://gts.x.test13.mconstdel.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mconstdel.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"indexed": None},
            },
            "register descendant trying to delete indexed",
        ),
        _validate_type_schema(
            "gts.x.test13.mconstdel.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - required prevents const-lock deletion",
        ),
    ]


class TestCaseOp13_Merge_NestedConstLock_ParentRequired_NullDeleteFails(HttpRunner):
    """ADR-0004: a nested lock holds when every path segment is required.

    `routing.indexed` is const-locked and required inside `routing`, and
    `routing` is required at the root. Deleting the parent with a single `null`
    patch removes the whole subtree, so the materialized object fails the root
    `required` — the lock survives because the path is required end to end.
    """

    config = Config("OP#13 ADR-0004: nested lock holds on required path").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnestlock.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "required": ["routing"],
                    "properties": {
                        "routing": {
                            "type": "object",
                            "required": ["indexed"],
                            "properties": {
                                "indexed": {"type": "boolean", "const": True},
                            },
                        },
                    },
                },
                "x-gts-traits": {"routing": {"indexed": True}},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base - routing required, routing.indexed const-locked",
        ),
        _register_derived(
            "gts://gts.x.test13.mnestlock.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnestlock.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"routing": None},
            },
            "register descendant deleting the whole routing subtree",
        ),
        _validate_type_schema(
            "gts.x.test13.mnestlock.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - root required blocks parent deletion",
        ),
    ]


class TestCaseOp13_Merge_NestedConstLock_ParentOptional_NullDeleteOk(HttpRunner):
    """ADR-0004: requiring only the leaf is not a lock.

    Same nested `const` + `required` on `routing.indexed`, but `routing` itself
    is optional. Deleting the parent removes the subtree, and the nested
    constraints never apply because their object is gone. The registry MUST NOT
    add a path-aware guard: this is a legal merge, so OP#13 passes.
    """

    config = Config("OP#13 ADR-0004: optional parent defeats nested lock").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnestopt.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "required": ["indexed"],
                            "properties": {
                                "indexed": {"type": "boolean", "const": True},
                            },
                        },
                    },
                },
                "x-gts-traits": {"routing": {"indexed": True}},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base - routing optional, routing.indexed const-locked",
        ),
        _register_derived(
            "gts://gts.x.test13.mnestopt.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnestopt.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"routing": None},
            },
            "register descendant deleting the optional routing parent",
        ),
        _validate_type_schema(
            "gts.x.test13.mnestopt.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - nested constraints vanish with their parent",
        ),
    ]


class TestCaseOp13_Merge_ConstLock_IdempotentRestatementOk(HttpRunner):
    """ADR-0004: descendant restates const-locked value. Passes."""

    config = Config("OP#13 ADR-0004: const lock idempotent restatement").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mconstid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "indexed": {"type": "boolean", "const": True},
                    },
                    "required": ["indexed"],
                },
                "x-gts-traits": {"indexed": True},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with const-locked indexed=true",
        ),
        _register_derived(
            "gts://gts.x.test13.mconstid.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mconstid.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"indexed": True},
            },
            "register descendant restating indexed=true",
        ),
        _validate_type_schema(
            "gts.x.test13.mconstid.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - idempotent restatement allowed",
        ),
    ]


class TestCaseOp13_Merge_IdempotentScalarRestatement(HttpRunner):
    """ADR-0004 §"Conformance test suite" (e): idempotent restatement of a scalar.

    Descendant repeats the ancestor's value verbatim — merge yields the same
    value; passes. Documents that the deleted "MUST fail on identical
    restatement" interpretation is gone.
    """

    config = Config("OP#13 ADR-0004: idempotent scalar restatement").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.midemp.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base retention=P30D",
        ),
        _register_derived(
            "gts://gts.x.test13.midemp.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.midemp.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P30D"},
            },
            "register descendant restating retention=P30D",
        ),
        _validate_type_schema(
            "gts.x.test13.midemp.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - idempotent restatement passes",
        ),
    ]


class TestCaseOp13_TraitsValueViolatesIntegerSchema(HttpRunner):
    """ADR-0002 successor to the deleted TraitsSchemaNotObject case.

    x-gts-traits-schema is an object subschema with `type:object`, declaring
    a single `count` property of type:integer. The deleted case rejected the
    base because the old §9.7 gate required `x-gts-traits-schema` to declare
    `type: object` at the top level and treated *any* non-object form as a
    registration-time failure. ADR-0002 lifts that gate — the value space is
    now subschema OR `true` OR `false`. Note the spec still requires the
    *effective* (chain-aggregated) trait-schema to constrain trait values to
    JSON objects when expressed in object subschema form (README §9.7), so a
    bare top-level `{type: integer}` remains practically unsatisfiable — but
    a property-level integer constraint (as here) is fine. What this test
    exercises is the value-side enforcement that remains: a descendant
    supplying a non-integer for `count` MUST fail JSON Schema validation
    against the effective trait-schema.
    """

    config = Config("OP#13 ADR-0002: trait value violates integer schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mintsch.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"count": {"type": "integer"}},
                    "required": ["count"],
                },
                "x-gts-traits": {"count": 7},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with integer-typed count and value 7",
        ),
        _register_derived(
            "gts://gts.x.test13.mintsch.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mintsch.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"count": "not-an-int"},
            },
            "register descendant with non-integer count",
        ),
        _validate_type_schema(
            "gts.x.test13.mintsch.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - value fails integer schema",
        ),
    ]


class TestCaseOp13_Merge_NestedNullDelete_PreservesPeer(HttpRunner):
    """ADR-0004 Worked example B (null-at-nested-depth variant).

    Base sets `routing: {topic, partitionKey}`; descendant writes
    `routing: {partitionKey: null}`. RFC 7396 descends into `routing` and
    deletes `partitionKey` at the leaf, while preserving the peer key
    `topic`. The trait-schema requires only `topic` inside `routing`, so
    completeness passes.

    This case visibly distinguishes RFC 7396 (Option 2c) from shallow
    last-wins (Option 2a): under shallow merge the descendant's `routing`
    object would replace the ancestor's wholesale, giving an effective
    `routing` with no `topic` at all — completeness would fail. Recursive
    merge descends into `routing`, applies `partitionKey: null` as a leaf
    delete, and keeps the ancestor's `topic`.
    """

    config = Config("OP#13 ADR-0004: nested null-delete preserves peer").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnestnull.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "partitionKey": {"type": "string"},
                            },
                            "required": ["topic"],
                        },
                    },
                    "required": ["routing"],
                },
                "x-gts-traits": {
                    "routing": {"topic": "events", "partitionKey": "userId"},
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with routing.{topic, partitionKey}",
        ),
        _register_derived(
            "gts://gts.x.test13.mnestnull.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnestnull.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "routing": {"partitionKey": None},
                },
            },
            "register descendant deleting only routing.partitionKey",
        ),
        _validate_type_schema(
            "gts.x.test13.mnestnull.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - routing.topic preserved by recursive merge",
        ),
    ]


class TestCaseOp13_Merge_ConstLock_PreservedAcrossDescendant(HttpRunner):
    """ADR-0004 Worked example C, Descendant A: const-locked value flows down.

    Trait-schema declares `indexed: {const: true}` and `retention` open.
    Base sets `indexed: true` and `retention: P30D`. Descendant overrides
    ONLY `retention`; it does NOT restate `indexed`. RFC 7396 merge
    preserves `indexed: true` from the chain; the materialized effective
    traits object satisfies `const: true` for `indexed` and the descendant's
    new retention value. Validation passes — the publisher's lock holds
    naturally, without requiring the descendant to know about it.
    """

    config = Config("OP#13 ADR-0004: const-locked value preserved across descendant").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mconstpres.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "indexed": {"type": "boolean", "const": True},
                        "retention": {"type": "string"},
                    },
                    "required": ["indexed", "retention"],
                },
                "x-gts-traits": {"indexed": True, "retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with const-locked indexed and open retention",
        ),
        _register_derived(
            "gts://gts.x.test13.mconstpres.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mconstpres.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P365D"},
            },
            "register descendant overriding only retention",
        ),
        _validate_type_schema(
            "gts.x.test13.mconstpres.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - const-locked indexed preserved from chain",
        ),
    ]


# ---------------------------------------------------------------------------
# ADR-0002: additional x-gts-traits-schema value-space / aggregation coverage
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitsSchema_NonObjectEffective_RejectsTraits(HttpRunner):
    """ADR-0002 / README §9.7: a non-object effective trait-schema rejects traits.

    The value space now admits any subschema, but §9.7 still requires the
    *effective* object-form trait-schema to constrain trait values to JSON
    objects. A bare `{type: integer}` effective trait-schema can therefore
    never be satisfied by an `x-gts-traits` object — the traits value is a JSON
    object, which is not an integer. This is the behavioral backstop that
    replaced the deleted syntactic `TraitsSchemaNotObject` gate (which the
    successor integer-property case did not directly cover). Validation fails.
    """

    config = Config("OP#13 ADR-0002: non-object effective trait-schema rejects traits").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.nonobjts.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {"type": "integer"},
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base whose effective trait-schema is {type:integer}",
        ),
        _validate_type_schema(
            "gts.x.test13.nonobjts.event.v1~",
            False,
            "validate - traits object cannot satisfy a non-object effective schema",
        ),
    ]


class TestCaseOp13_TraitsSchema_BooleanFalse_AtLeaf_OptOut_Fails(HttpRunner):
    """ADR-0002: a leaf may opt out by declaring `x-gts-traits-schema: false`.

    ADR-0002 calls out the leaf opt-out explicitly. The base declares a
    permissive object trait-schema; the descendant declares `false` AND still
    carries `x-gts-traits`. The chain-aggregated effective schema is
    `allOf(object-schema, false)` = false, so any traits are rejected.
    Counterpart to BooleanFalse_DescendantSetsTraits, with `false` at the leaf.
    """

    config = Config("OP#13 ADR-0002: false at leaf opt-out rejects traits").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.falseleaf.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with permissive object trait-schema",
        ),
        _register_derived(
            "gts://gts.x.test13.falseleaf.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.falseleaf.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": False,
                "x-gts-traits": {"retention": "P7D"},
            },
            "register leaf declaring traits-schema false but still carrying traits",
        ),
        _validate_type_schema(
            "gts.x.test13.falseleaf.event.v1~x.test13._.kid.v1~",
            False,
            "validate leaf - false makes effective schema unsatisfiable",
        ),
    ]


class TestCaseOp13_TraitsSchema_BooleanTrue_Identity_DescendantConstrains(HttpRunner):
    """ADR-0002: `true` is the identity element under allOf aggregation.

    Base declares `x-gts-traits-schema: true` (admits anything). The descendant
    introduces an object trait-schema with a required property and supplies its
    value. The effective schema is `allOf(true, {object})` = the object schema;
    `true` contributes nothing. Validation passes. Symmetric positive companion
    to the well-covered `false` aggregation cases.
    """

    config = Config("OP#13 ADR-0002: true is identity in aggregation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.trueid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": True,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with traits-schema true",
        ),
        _register_derived(
            "gts://gts.x.test13.trueid.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.trueid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
                "x-gts-traits": {"topicRef": "events.orders"},
            },
            "register descendant adding object trait-schema + value",
        ),
        _validate_type_schema(
            "gts.x.test13.trueid.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - true contributed nothing, object schema satisfied",
        ),
    ]


# ---------------------------------------------------------------------------
# ADR-0003: additional completeness × abstract boundary coverage
# ---------------------------------------------------------------------------


class TestCaseOp13_Completeness_AbstractDroppedByConcreteDescendant_Fails(HttpRunner):
    """ADR-0003 + §9.11.3(4): abstractness does not propagate.

    Abstract A declares a required trait with no default (completeness skipped).
    Concrete B derives from A, does NOT declare x-gts-abstract, and does NOT
    resolve the required trait. Because a derived type is concrete by default,
    B MUST satisfy completeness — and fails. This is the symmetric failure
    counterpart to AbstractBase_ConcreteDescendantSatisfies.
    """

    config = Config("OP#13 ADR-0003: concrete descendant of abstract must complete").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.absdrop.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base with unresolved required trait",
        ),
        _register_derived(
            "gts://gts.x.test13.absdrop.event.v1~x.test13._.concrete.v1~",
            "gts://gts.x.test13.absdrop.event.v1~",
            {
                "type": "object",
            },
            "register concrete descendant that does NOT resolve the trait",
        ),
        _validate_type_schema(
            "gts.x.test13.absdrop.event.v1~",
            True,
            "validate abstract base via validate-type-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.absdrop.event.v1~x.test13._.concrete.v1~",
            False,
            "validate concrete descendant - inherited required trait unresolved",
        ),
    ]


class TestCaseOp13_Completeness_AbstractIntermediate_NonAbstractLeafMustComplete(HttpRunner):
    """ADR-0003: an abstract intermediate is skipped, but a non-abstract leaf is not.

    Chain R → M → L. R is concrete with no traits (trivially complete). M is
    abstract and introduces a required trait with no default — its completeness
    is skipped. L is non-abstract and does NOT resolve the trait, so L fails.
    Validating M passes (skipped); validating L fails. Confirms the rule keys on
    each type's own x-gts-abstract, independent of chain position.
    """

    config = Config("OP#13 ADR-0003: abstract intermediate, leaf must complete").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.absint.event.v1~",
            {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register concrete root R with no traits",
        ),
        _register_derived(
            "gts://gts.x.test13.absint.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.absint.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                    "required": ["topicRef"],
                },
            },
            "register abstract mid M introducing an unresolved required trait",
            top_level={"x-gts-abstract": True},
        ),
        _register_derived(
            (
                "gts://gts.x.test13.absint.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.absint.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
            },
            "register non-abstract leaf L that does NOT resolve the trait",
        ),
        _validate_type_schema(
            "gts.x.test13.absint.event.v1~x.test13._.mid.v1~",
            True,
            "validate abstract intermediate M - completeness skipped",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.absint.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            False,
            "validate non-abstract leaf L - inherited required trait unresolved",
        ),
    ]


class TestCaseOp13_Completeness_DefaultIntroducedByIntermediate_SatisfiesLeaf(HttpRunner):
    """ADR-0003: a default introduced by an intermediate can close a leaf's required.

    Abstract base A declares a required trait with no default (skipped). A
    concrete intermediate M redeclares the trait-schema adding a `default` (a
    free annotation per §9.7.5). A non-abstract leaf L supplies no value; during
    materialization the intermediate's default fills the required trait, so L is
    complete. Validation of L passes.
    """

    config = Config("OP#13 ADR-0003: default from intermediate satisfies leaf").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.dflmid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base A - required retention, no default",
        ),
        _register_derived(
            "gts://gts.x.test13.dflmid.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.dflmid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string", "default": "P7D"}},
                },
            },
            "register concrete mid M redeclaring trait-schema with a default",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.dflmid.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.dflmid.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
            },
            "register non-abstract leaf L with no value - relies on the default",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.dflmid.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            True,
            "validate leaf - intermediate's default materializes the required trait",
        ),
    ]


# ---------------------------------------------------------------------------
# ADR-0004: additional RFC 7396 merge coverage (recurse-vs-replace boundary,
# null-on-container, effective-value discrimination, depth-3 enforcement)
# ---------------------------------------------------------------------------


class TestCaseOp13_Merge_TypeChange_ObjectReplacedByScalar_AbstractBase(HttpRunner):
    """ADR-0004 / RFC 7396: a non-object patch value replaces wholesale (no recursion).

    Abstract base sets an object-valued `routing`; the trait-schema constrains
    `routing` to a string. The base is invalid because abstractness skips
    completeness but does not permit an explicitly invalid value. Although the
    descendant replaces the object with a string, transitive validation fails
    because its abstract ancestor is invalid.
    """

    config = Config("OP#13 ADR-0004: abstract object trait replaced by scalar").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.mtchg.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"routing": {"type": "string"}},
                    "required": ["routing"],
                },
                "x-gts-traits": {"routing": {"topic": "t", "partitionKey": "k"}},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base - routing is an object",
        ),
        _register_derived(
            "gts://gts.x.test13.mtchg.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mtchg.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"routing": "flat-string"},
            },
            "register descendant replacing routing with a scalar string",
        ),
        _validate_type_schema(
            "gts.x.test13.mtchg.event.v1~",
            False,
            "validate abstract base - provided routing has wrong type",
        ),
        _validate_type_schema(
            "gts.x.test13.mtchg.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - abstract ancestor is invalid",
        ),
    ]


class TestCaseOp13_Merge_TypeChange_ObjectReplacedByScalar_ValidBase(HttpRunner):
    """Object-to-scalar replacement is isolated from ancestor validity.

    The valid base permits object or string routing and supplies an object. The
    descendant narrows routing to string and supplies a scalar. Replacing the
    object makes the descendant valid; retaining or recursively merging the
    object violates the descendant's string constraint.
    """

    config = Config("OP#13 ADR-0004: valid object trait replaced by scalar").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mtchgvalid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"routing": {"type": ["object", "string"]}},
                    "required": ["routing"],
                },
                "x-gts-traits": {"routing": {"topic": "t", "partitionKey": "k"}},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register valid base with object routing",
        ),
        _register_derived(
            "gts://gts.x.test13.mtchgvalid.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mtchgvalid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"routing": {"type": "string"}},
                },
                "x-gts-traits": {"routing": "flat-string"},
            },
            "register descendant replacing routing with a scalar string",
        ),
        _validate_type_schema(
            "gts.x.test13.mtchgvalid.event.v1~",
            True,
            "validate base - object routing is allowed",
        ),
        _validate_type_schema(
            "gts.x.test13.mtchgvalid.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - scalar replaced the object wholesale",
        ),
    ]


class TestCaseOp13_Merge_TypeChange_ClosedObjectInvalidBase(HttpRunner):
    """A nested closed trait object rejects undeclared base values.

    The base permits object or string routing, but its object form declares only
    `topic` and sets `additionalProperties: false`. Its supplied `partitionKey`
    makes the base invalid. Replacing routing with a valid scalar in the
    descendant cannot repair that invalid ancestor.
    """

    config = Config("OP#13 ADR-0004: closed routing object invalid base").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mtchgclosed.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": ["object", "string"],
                            "additionalProperties": False,
                            "properties": {"topic": {"type": "string"}},
                        },
                    },
                    "required": ["routing"],
                },
                "x-gts-traits": {"routing": {"topic": "t", "partitionKey": "k"}},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register invalid base with prohibited partitionKey",
        ),
        _register_derived(
            "gts://gts.x.test13.mtchgclosed.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mtchgclosed.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"routing": {"type": "string"}},
                },
                "x-gts-traits": {"routing": "flat-string"},
            },
            "register descendant replacing routing with a scalar string",
        ),
        _validate_type_schema(
            "gts.x.test13.mtchgclosed.event.v1~",
            False,
            "validate base - partitionKey is an additional property",
        ),
        _validate_type_schema(
            "gts.x.test13.mtchgclosed.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - closed-object base is invalid",
        ),
    ]


class TestCaseOp13_Merge_NullDelete_WholeObjectKey_Fails(HttpRunner):
    """ADR-0004 / RFC 7396: `null` deletes a whole object-valued key.

    Ancestor sets an object-valued required `routing`; the trait-schema requires
    it and provides no default. A non-abstract descendant writes `routing: null`,
    which deletes the entire key (not just nested fields). Completeness then
    fails because a required trait is unresolved with no default. Counterpart to
    the scalar null-delete case at object granularity.
    """

    config = Config("OP#13 ADR-0004: null deletes whole object key").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnullobj.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "properties": {"topic": {"type": "string"}},
                        },
                    },
                    "required": ["routing"],
                },
                "x-gts-traits": {"routing": {"topic": "t"}},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with required object-valued routing, no default",
        ),
        _register_derived(
            "gts://gts.x.test13.mnullobj.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnullobj.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"routing": None},
            },
            "register descendant nulling the whole routing object",
        ),
        _validate_type_schema(
            "gts.x.test13.mnullobj.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - whole required object key deleted, no default",
        ),
    ]


class TestCaseOp13_Merge_NullDelete_FallsBackToDefault_AbstractBase(HttpRunner):
    """ADR-0004 + ADR-0003: null-delete on an invalid abstract base.

    The trait-schema locks `retention` with `const: P7D` and a matching default.
    The abstract base supplies `retention: P30D`, so it is invalid: abstractness
    skips completeness but not validation of provided values. The descendant
    deletes P30D, but transitive validation still fails on the invalid ancestor.
    """

    config = Config("OP#13 ADR-0004: abstract null-delete reverts to default").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.mnulldef.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"const": "P7D", "default": "P7D"},
                    },
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base - retention P30D",
        ),
        _register_derived(
            "gts://gts.x.test13.mnulldef.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnulldef.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": None},
            },
            "register descendant nulling retention",
        ),
        _validate_type_schema(
            "gts.x.test13.mnulldef.event.v1~",
            False,
            "validate abstract base - provided retention violates const",
        ),
        _validate_type_schema(
            "gts.x.test13.mnulldef.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - abstract ancestor is invalid",
        ),
    ]


class TestCaseOp13_Merge_NullDelete_FallsBackToDefault_ValidBase(HttpRunner):
    """Null deletion and default materialization with a valid dependency chain.

    The valid base supplies `retention: P30D`. The descendant narrows the trait
    with `const: P7D` and a matching default, then deletes the inherited value.
    Correct deletion materializes P7D; treating null as a no-op retains P30D and
    violates the descendant constraint.
    """

    config = Config("OP#13 ADR-0004: valid null-delete reverts to default").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnulldefvalid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string"},
                    },
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register valid base with retention P30D",
        ),
        _register_derived(
            "gts://gts.x.test13.mnulldefvalid.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnulldefvalid.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"const": "P7D", "default": "P7D"},
                    },
                },
                "x-gts-traits": {"retention": None},
            },
            "register descendant nulling retention",
        ),
        _validate_type_schema(
            "gts.x.test13.mnulldefvalid.event.v1~",
            True,
            "validate base - retention P30D satisfies its schema",
        ),
        _validate_type_schema(
            "gts.x.test13.mnulldefvalid.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - null deletion materializes P7D",
        ),
    ]


class TestCaseOp13_Merge_NullDelete_OptionalKey_NonAbstract_Ok(HttpRunner):
    """ADR-0004: null-deleting an optional key on a non-abstract type succeeds.

    The benign positive companion to the required-key delete cases. The trait is
    optional (not in `required`); a non-abstract descendant null-deletes it. The
    key simply becomes absent and completeness still holds. Validation passes.
    """

    config = Config("OP#13 ADR-0004: null-delete optional key ok").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnullopt.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"note": {"type": "string"}},
                },
                "x-gts-traits": {"note": "hello"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with an optional note trait set",
        ),
        _register_derived(
            "gts://gts.x.test13.mnullopt.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnullopt.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"note": None},
            },
            "register descendant nulling the optional note",
        ),
        _validate_type_schema(
            "gts.x.test13.mnullopt.event.v1~x.test13._.kid.v1~",
            True,
            "validate descendant - optional key deleted, still complete",
        ),
    ]


class TestCaseOp13_Merge_NestedArrayReplacedWholesale_PeerPreserved(HttpRunner):
    """ADR-0004 / RFC 7396: arrays replace wholesale at any depth, peers still merge.

    `routing` is an object trait with a peer string `topic` and an array
    `partitions` (`minItems: 2`). The base sets both; the descendant restates
    only `routing.partitions` with a single-element array. Recursive object merge
    preserves the peer `topic`, while the nested array is replaced wholesale
    (not unioned), leaving 1 element < minItems 2. Validation fails — proving
    nested-array replacement combined with peer-object preservation. The base
    itself (3 elements) is complete and validates.
    """

    config = Config("OP#13 ADR-0004: nested array replaced wholesale").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mnestarr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "routing": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "partitions": {"type": "array", "minItems": 2},
                            },
                            "required": ["topic", "partitions"],
                        },
                    },
                    "required": ["routing"],
                },
                "x-gts-traits": {
                    "routing": {"topic": "t", "partitions": ["a", "b", "c"]},
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base - routing with topic + 3-element partitions",
        ),
        _register_derived(
            "gts://gts.x.test13.mnestarr.event.v1~x.test13._.kid.v1~",
            "gts://gts.x.test13.mnestarr.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"routing": {"partitions": ["only-one"]}},
            },
            "register descendant restating only routing.partitions (1 element)",
        ),
        _validate_type_schema(
            "gts.x.test13.mnestarr.event.v1~",
            True,
            "validate base - 3-element partitions satisfies minItems",
        ),
        _validate_type_schema(
            "gts.x.test13.mnestarr.event.v1~x.test13._.kid.v1~",
            False,
            "validate descendant - nested array replaced (1<2), peer topic preserved",
        ),
    ]


class TestCaseOp13_Merge_ConstLock_Depth3_MidRestatesLeafViolates(HttpRunner):
    """ADR-0004: const lock is enforced across a 3-level chain.

    Base locks `indexed` with `const: true`. The mid restates `indexed: true`
    (idempotent, allowed). The leaf attempts `indexed: false`, which violates the
    const constraint carried in the effective trait-schema. Validating the mid
    passes; validating the leaf fails. Extends the 2-level const cases to depth 3.
    """

    config = Config("OP#13 ADR-0004: const lock enforced at depth 3").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mconst3.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"indexed": {"const": True}},
                    "required": ["indexed"],
                },
                "x-gts-traits": {"indexed": True},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base locking indexed const:true",
        ),
        _register_derived(
            "gts://gts.x.test13.mconst3.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.mconst3.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"indexed": True},
            },
            "register mid restating indexed:true (idempotent)",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.mconst3.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.mconst3.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {"indexed": False},
            },
            "register leaf attempting indexed:false",
        ),
        _validate_type_schema(
            "gts.x.test13.mconst3.event.v1~x.test13._.mid.v1~",
            True,
            "validate mid - idempotent restatement of the locked value",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.mconst3.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            False,
            "validate leaf - indexed:false violates const at depth 3",
        ),
    ]


class TestCaseOp13_Merge_3Layer_DistinctKeysAccumulate(HttpRunner):
    """A non-abstract incomplete intermediate invalidates its descendant.

    The abstract base sets `a`; the non-abstract mid adds `b` but leaves `c`
    unresolved and is therefore invalid. The leaf adds `c` and is locally
    complete, but transitive validation fails on its invalid intermediate.
    """

    config = Config("OP#13 ADR-0004: incomplete mid invalidates leaf").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.macc.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string"},
                        "b": {"type": "string"},
                        "c": {"type": "string"},
                    },
                    "required": ["a", "b", "c"],
                },
                "x-gts-traits": {"a": "va"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base setting a",
        ),
        _register_derived(
            "gts://gts.x.test13.macc.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.macc.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"b": "vb"},
            },
            "register non-abstract mid setting b but not c",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.macc.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.macc.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {"c": "vc"},
            },
            "register locally complete leaf setting c",
        ),
        _validate_type_schema(
            "gts.x.test13.macc.event.v1~x.test13._.mid.v1~",
            False,
            "validate mid - non-abstract type has unresolved c",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.macc.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            False,
            "validate leaf - intermediate ancestor is invalid",
        ),
    ]


class TestCaseOp13_Merge_3Layer_AbstractDistinctKeysAccumulate(HttpRunner):
    """Distinct keys accumulate through valid abstract intermediate types.

    The abstract base and mid may remain incomplete while setting `a` and `b`.
    The concrete leaf adds `c`; its effective traits contain all three required
    values, and every ancestor is valid.
    """

    config = Config("OP#13 ADR-0004: abstract chain accumulates distinct keys").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_abstract(
            "gts://gts.x.test13.maccabs.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string"},
                        "b": {"type": "string"},
                        "c": {"type": "string"},
                    },
                    "required": ["a", "b", "c"],
                },
                "x-gts-traits": {"a": "va"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base setting a",
        ),
        _register_derived(
            "gts://gts.x.test13.maccabs.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.maccabs.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"b": "vb"},
            },
            "register abstract mid setting b",
            top_level={"x-gts-abstract": True},
        ),
        _register_derived(
            (
                "gts://gts.x.test13.maccabs.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.maccabs.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {"c": "vc"},
            },
            "register concrete leaf setting c",
        ),
        _validate_type_schema(
            "gts.x.test13.maccabs.event.v1~",
            True,
            "validate abstract base - unresolved b and c are allowed",
        ),
        _validate_type_schema(
            "gts.x.test13.maccabs.event.v1~x.test13._.mid.v1~",
            True,
            "validate abstract mid - unresolved c is allowed",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.maccabs.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            True,
            "validate leaf - distinct keys from all layers accumulated",
        ),
    ]


class TestCaseOp13_Merge_DeleteThenReadd_AcrossLayers(HttpRunner):
    """ADR-0004 / RFC 7396: a key deleted by a mid layer can be re-added by the leaf.

    Base sets `retention`; the mid null-deletes it; the leaf sets it again to a
    concrete value. The leaf's restatement wins (last-wins) and the required
    trait is resolved, so validation passes. Exercises delete-then-re-add merge
    ordering across three layers.
    """

    config = Config("OP#13 ADR-0004: delete-then-readd across layers").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.mreadd.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
                "x-gts-traits": {"retention": "P30D"},
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with retention P30D",
        ),
        _register_derived(
            "gts://gts.x.test13.mreadd.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.mreadd.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": None},
            },
            "register abstract mid deleting retention",
            top_level={"x-gts-abstract": True},
        ),
        _register_derived(
            (
                "gts://gts.x.test13.mreadd.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            "gts://gts.x.test13.mreadd.event.v1~x.test13._.mid.v1~",
            {
                "type": "object",
                "x-gts-traits": {"retention": "P90D"},
            },
            "register leaf re-adding retention P90D",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.mreadd.event.v1~"
                "x.test13._.mid.v1~x.test13._.leaf.v1~"
            ),
            True,
            "validate leaf - retention re-added after mid deleted it",
        ),
    ]


# ---------------------------------------------------------------------------
# x-gts-ref resolution inside x-gts-traits values (issue #107)
#
# When a trait-schema property declares x-gts-ref, the concrete value
# provided in x-gts-traits MUST be validated against the reference:
#   - the value must be a syntactically valid GTS identifier, AND
#   - the referenced entity must be registered in the registry.
#
# These tests exercise both the positive path (registered topic) and the
# negative path (nonexistent topic) for a topicRef trait annotated with
# x-gts-ref.
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitRef_TopicRefValid(HttpRunner):
    """OP#13 / x-gts-ref in traits: topicRef points to a registered topic.

    Registers a topic type schema, a topic instance, and an event type whose
    x-gts-traits.topicRef resolves to that topic. Validation must pass.
    """

    config = Config(
        "OP#13 x-gts-ref: topicRef resolves to registered topic"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register topic type schema
        _register(
            "gts://gts.x.test13.tref.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic type schema",
        ),
        # Register a concrete topic instance
        _register_instance(
            {
                "id": (
                    "gts.x.test13.tref.topic.v1~"
                    "x.test13._.orders.v1"
                ),
                "name": "orders",
            },
            "register topic instance (orders)",
        ),
        # Register event base with trait-schema declaring topicRef + x-gts-ref
        _register(
            "gts://gts.x.test13.tref.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.tref.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register event base with topicRef trait (x-gts-ref)",
        ),
        # Derived event: topicRef points to the registered topic
        _register_derived(
            (
                "gts://gts.x.test13.tref.event.v1~"
                "x.test13._.order_placed.v1~"
            ),
            "gts://gts.x.test13.tref.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.tref.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                    "retention": "P90D",
                },
            },
            "register derived with topicRef to registered topic",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.tref.event.v1~"
                "x.test13._.order_placed.v1~"
            ),
            True,
            "validate - topicRef resolves to registered topic, should pass",
        ),
    ]


class TestCaseOp13_TraitRef_TopicRefNonexistent(HttpRunner):
    """OP#13 / x-gts-ref in traits: topicRef points to a nonexistent topic.

    The topicRef value has valid GTS syntax and correct prefix, but the
    referenced entity does not exist in the registry. Validation must fail.
    This is the regression scenario described in issue #107.
    """

    config = Config(
        "OP#13 x-gts-ref: topicRef to nonexistent topic fails"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Reuse the same topic type schema (may already be registered)
        _register(
            "gts://gts.x.test13.tref.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic type schema (idempotent)",
        ),
        # Register event base with trait-schema declaring topicRef + x-gts-ref
        _register(
            "gts://gts.x.test13.trefm.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.tref.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register event base with topicRef trait (x-gts-ref)",
        ),
        # Derived event: topicRef points to a topic that does NOT exist
        _register_derived(
            (
                "gts://gts.x.test13.trefm.event.v1~"
                "x.test13._.order_placed_bad.v1~"
            ),
            "gts://gts.x.test13.trefm.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.tref.topic.v1~"
                        "x.test13._.nonexistent_topic.v12.0"
                    ),
                    "retention": "P90D",
                },
            },
            "register derived with topicRef to nonexistent topic",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.trefm.event.v1~"
                "x.test13._.order_placed_bad.v1~"
            ),
            False,
            "validate should fail - topicRef references nonexistent topic",
        ),
    ]


class TestCaseOp13_TraitRef_MalformedValues(HttpRunner):
    """OP#13 / x-gts-ref in traits: malformed topicRef values must fail.

    Exercises three classes of bad values in x-gts-traits for a property
    annotated with x-gts-ref:
      - not a GTS identifier at all (plain string)
      - partial / syntactically invalid GTS identifier (too few segments)
      - valid GTS identifier but wrong prefix (doesn't match x-gts-ref)
    """

    config = Config(
        "OP#13 x-gts-ref: malformed trait ref values rejected"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register topic type schema (the x-gts-ref target type)
        _register(
            "gts://gts.x.test13.tref.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic type schema (idempotent)",
        ),
        # Register event base with topicRef trait annotated with x-gts-ref
        _register(
            "gts://gts.x.test13.trefbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.tref.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register event base with topicRef trait (x-gts-ref)",
        ),
        # --- Case 1: not a GTS identifier at all ---
        _register_derived(
            (
                "gts://gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_plain_string.v1~"
            ),
            "gts://gts.x.test13.trefbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": "hello world",
                    "retention": "P90D",
                },
            },
            "register derived - topicRef is plain string",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_plain_string.v1~"
            ),
            False,
            "reject - topicRef 'hello world' is not a GTS identifier",
        ),
        # --- Case 2: partial / invalid GTS syntax (too few segments) ---
        _register_derived(
            (
                "gts://gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_partial_gts.v1~"
            ),
            "gts://gts.x.test13.trefbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": "gts.x.y.z",
                    "retention": "P90D",
                },
            },
            "register derived - topicRef is invalid GTS syntax",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_partial_gts.v1~"
            ),
            False,
            "reject - topicRef 'gts.x.y.z' is not a valid GTS identifier",
        ),
        # --- Case 3: valid GTS identifier but wrong prefix ---
        _register_derived(
            (
                "gts://gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_wrong_prefix.v1~"
            ),
            "gts://gts.x.test13.trefbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.other.namespace.thing.v1~"
                        "x.other._.some_topic.v1"
                    ),
                    "retention": "P90D",
                },
            },
            "register derived - topicRef has wrong prefix",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_wrong_prefix.v1~"
            ),
            False,
            "reject - topicRef prefix doesn't match x-gts-ref declaration",
        ),
        # --- Case 4: empty string ---
        _register_derived(
            (
                "gts://gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_empty.v1~"
            ),
            "gts://gts.x.test13.trefbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": "",
                    "retention": "P90D",
                },
            },
            "register derived - topicRef is empty string",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.trefbad.event.v1~"
                "x.test13._.bad_empty.v1~"
            ),
            False,
            "reject - topicRef empty string is not a valid GTS identifier",
        ),
    ]


_STANDARD_TRAIT_FORMAT_TYPE_ID = "gts.x.test13.formats.event.v1~"
_STANDARD_TRAIT_FORMATS = (
    ("uuidValue", "uuid", "550e8400-e29b-41d4-a716-446655440000", "not-a-uuid"),
    ("emailValue", "email", "user@example.com", "not-an-email"),
    ("dateTimeValue", "date-time", "2025-01-15T10:30:00Z", "not-date-time"),
    ("dateValue", "date", "2025-01-15", "2025-13-40"),
    ("timeValue", "time", "10:30:00Z", "25:99:99Z"),
    ("uriValue", "uri", "https://example.com/resource", "://not-a-uri"),
    ("hostnameValue", "hostname", "example.com", "not a hostname"),
    ("ipv4Value", "ipv4", "192.168.1.1", "999.999.999.999"),
    ("ipv6Value", "ipv6", "2001:db8::1", "not-an-ipv6-address"),
)
_STANDARD_TRAIT_FORMAT_VALUES = {
    field: valid for field, _, valid, _ in _STANDARD_TRAIT_FORMATS
}
_STANDARD_TRAIT_FORMAT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        field: {"type": "string", "format": format_name}
        for field, format_name, _, _ in _STANDARD_TRAIT_FORMATS
    },
}


class TestCaseOp13_TraitsInvalid_StandardFormats(HttpRunner):
    """OP#13 - Enforce standard JSON Schema formats on trait properties.

    ``url`` is not a standard JSON Schema format; HTTPS URL values are covered
    by the standard ``uri`` format instead.
    """
    config = Config("OP#13 - Standard Trait Format Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            f"gts://{_STANDARD_TRAIT_FORMAT_TYPE_ID}",
            {
                "type": "object",
                "x-gts-traits-schema": _STANDARD_TRAIT_FORMAT_SCHEMA,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with standard trait formats",
        ),
        _register_derived(
            (
                f"gts://{_STANDARD_TRAIT_FORMAT_TYPE_ID}"
                "x.test13._.valid_formats.v1~"
            ),
            f"gts://{_STANDARD_TRAIT_FORMAT_TYPE_ID}",
            {
                "type": "object",
                "x-gts-traits": _STANDARD_TRAIT_FORMAT_VALUES,
            },
            "register derived with valid standard trait formats",
        ),
        _validate_type_schema(
            (
                f"{_STANDARD_TRAIT_FORMAT_TYPE_ID}"
                "x.test13._.valid_formats.v1~"
            ),
            True,
            "validate derived with valid standard trait formats",
        ),
        *[
            _register_derived(
                (
                    f"gts://{_STANDARD_TRAIT_FORMAT_TYPE_ID}"
                    f"x.test13._.invalid_{format_name.replace('-', '_')}.v1~"
                ),
                f"gts://{_STANDARD_TRAIT_FORMAT_TYPE_ID}",
                {
                    "type": "object",
                    "x-gts-traits": {
                        **_STANDARD_TRAIT_FORMAT_VALUES,
                        field: invalid,
                    },
                },
                f"register derived with invalid trait {format_name}",
            )
            for field, format_name, _, invalid in _STANDARD_TRAIT_FORMATS
        ],
        *[
            _validate_type_schema(
                (
                    f"{_STANDARD_TRAIT_FORMAT_TYPE_ID}"
                    f"x.test13._.invalid_{format_name.replace('-', '_')}.v1~"
                ),
                False,
                f"reject trait with invalid {format_name}",
            )
            for _, format_name, _, _ in _STANDARD_TRAIT_FORMATS
        ],
    ]


_REGEX_ECMA262_TRAIT_TYPE_ID = "gts.x.test13.formats.regexecma.v1~"
_REGEX_ECMA262_TRAIT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"regexValue": {"type": "string", "format": "regex"}},
}

# Strings that ARE valid ECMA 262 regular expressions. The Draft-07 `regex`
# format asserts that the value is a regular expression valid according to the
# ECMA 262 dialect (README §9.2, ADR-0005); effective trait values that are
# valid ECMA 262 regexes MUST pass OP#13 validation.
_REGEX_ECMA262_TRAIT_VALID = (
    ("anchored_class", "^[A-Za-z0-9]+$"),
    ("shorthand_bounded", "\\d{3}-\\d{4}"),
    ("group_alternation", "(foo|bar)+"),
    ("range_bounded", "[a-z]{1,3}"),
    ("nested_groups", "(a(b)?c)*"),
    ("class_shorthand", "[\\s\\S]*"),
)

# Strings that are NOT valid ECMA 262 regular expressions; effective trait
# values that fail the `regex` format MUST be rejected.
_REGEX_ECMA262_TRAIT_INVALID = (
    ("unterminated_class", "[unclosed"),
    ("unterminated_group", "(unclosed"),
    ("reversed_quantifier", "a{3,2}"),
    ("trailing_backslash", "\\"),
    ("leading_quantifier", "*abc"),
    ("dangling_quantifier", "a**"),
)


class TestCaseOp13_Traits_RegexEcma262(HttpRunner):
    """OP#13 - Enforce the Draft-07 `regex` format as an ECMA 262 assertion on traits.

    README §9.2 and ADR-0005 require `regex` to be asserted on effective trait
    values: a value is valid only when it is a regular expression valid according
    to the ECMA 262 regular expression dialect. Valid patterns must pass;
    strings that are not valid ECMA 262 regular expressions must be rejected.
    """
    config = Config("OP#13 - Regex ECMA 262 Trait Conformance").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            f"gts://{_REGEX_ECMA262_TRAIT_TYPE_ID}",
            {
                "type": "object",
                "x-gts-traits-schema": _REGEX_ECMA262_TRAIT_SCHEMA,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with regex trait format",
        ),
        *[
            _register_derived(
                (
                    f"gts://{_REGEX_ECMA262_TRAIT_TYPE_ID}"
                    f"x.test13._.regex_valid_{label}.v1~"
                ),
                f"gts://{_REGEX_ECMA262_TRAIT_TYPE_ID}",
                {
                    "type": "object",
                    "x-gts-traits": {"regexValue": pattern},
                },
                f"register derived with valid ECMA 262 regex trait ({label})",
            )
            for label, pattern in _REGEX_ECMA262_TRAIT_VALID
        ],
        *[
            _validate_type_schema(
                (
                    f"{_REGEX_ECMA262_TRAIT_TYPE_ID}"
                    f"x.test13._.regex_valid_{label}.v1~"
                ),
                True,
                f"accept valid ECMA 262 regex trait ({label})",
            )
            for label, _ in _REGEX_ECMA262_TRAIT_VALID
        ],
        *[
            _register_derived(
                (
                    f"gts://{_REGEX_ECMA262_TRAIT_TYPE_ID}"
                    f"x.test13._.regex_invalid_{label}.v1~"
                ),
                f"gts://{_REGEX_ECMA262_TRAIT_TYPE_ID}",
                {
                    "type": "object",
                    "x-gts-traits": {"regexValue": pattern},
                },
                f"register derived with invalid ECMA 262 regex trait ({label})",
            )
            for label, pattern in _REGEX_ECMA262_TRAIT_INVALID
        ],
        *[
            _validate_type_schema(
                (
                    f"{_REGEX_ECMA262_TRAIT_TYPE_ID}"
                    f"x.test13._.regex_invalid_{label}.v1~"
                ),
                False,
                f"reject invalid ECMA 262 regex trait ({label})",
            )
            for label, _ in _REGEX_ECMA262_TRAIT_INVALID
        ],
    ]


# ---------------------------------------------------------------------------
# x-gts-ref existence semantics for trait values (§9.6)
#
# §9.6 accepts two GTS constraint forms of x-gts-ref on a trait property:
#   - a WILDCARD pattern (e.g. "gts.*", "gts.cf.core.am.*", "...v1~*"): the
#     value must be a well-formed GTS id that matches the pattern (§10);
#   - a CONCRETE identifier (e.g. "gts.x.test13.xref....v1~"): the value must be
#     a well-formed GTS id that matches the constraint (a `~`-terminated
#     constraint matches the exact id and any derived id).
#
# Operand/value syntax and matching are always enforced. Registry lookup is
# skipped by `none`; `any-present` requires registered constraint and value targets;
# and `any-valid` additionally validates required targets. For wildcard constraints,
# `any-present` needs one registered match and `any-valid` needs one valid match.
#
# The inherited cases (a/b/c) below also exercise trait inheritance: an
# intermediate "audit" type supplies topicRef via x-gts-traits and is itself
# never validated; a further-derived "user" type inherits that value and is the
# one validated. Existence of the inherited value's target is resolved when the
# user type is validated.
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitRef_WildcardRequiresExistence(HttpRunner):
    """§9.6 wildcard: exercise registry existence under the default any-valid mode.

    A topicRef whose value is a well-formed GTS id that matches the pattern but
    is never registered fails; a value identifying a registered valid entity
    passes.
    """

    config = Config(
        "OP#13 x-gts-ref: gts.* wildcard enforces existence"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register a concrete topic the good value will resolve to.
        _register(
            "gts://gts.x.test13.xrefwild.topic.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register topic type the wildcard value will resolve to",
        ),
        _register_instance(
            {
                "id": (
                    "gts.x.test13.xrefwild.topic.v1~"
                    "x.test13._.orders.v1"
                ),
                "name": "orders",
            },
            "register topic instance (wildcard resolution target)",
        ),
        _register(
            "gts://gts.x.test13.xrefwild.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {"type": "string", "x-gts-ref": "gts.*"},
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with wildcard x-gts-ref topicRef",
        ),
        # --- Negative: value matches gts.* but is never registered ---
        _register_derived(
            "gts://gts.x.test13.xrefwild.event.v1~x.test13._.ghost.v1~",
            "gts://gts.x.test13.xrefwild.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.xrefwild.nowhere.v1~"
                        "x.test13._.ghost.v1"
                    ),
                },
            },
            "register derived with topicRef to a never-registered entity",
        ),
        _validate_type_schema(
            "gts.x.test13.xrefwild.event.v1~x.test13._.ghost.v1~",
            False,
            "validate - gts.* wildcard requires existence, nonexistent value fails",
        ),
        # --- Positive: value matches gts.* and resolves to a registered entity ---
        _register_derived(
            "gts://gts.x.test13.xrefwild.event.v1~x.test13._.leaf.v1~",
            "gts://gts.x.test13.xrefwild.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.xrefwild.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                },
            },
            "register derived with topicRef to a registered entity",
        ),
        _validate_type_schema(
            "gts.x.test13.xrefwild.event.v1~x.test13._.leaf.v1~",
            True,
            "validate - gts.* wildcard value resolves to a registered entity, passes",
        ),
    ]


class TestCaseOp13_TraitRef_UnsupportedPointers(HttpRunner):
    """Trait x-gts-ref operands may not use pointers other than /$id."""

    config = Config("OP#13 x-gts-ref: reject trait pointers").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject trait pointer to concrete constraint metadata")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test13.xrefrel.event.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "constraintType": "gts.x.test13.xrefrel.topic.v1~",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "/x-gts-traits-schema/constraintType",
                        },
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("reject missing trait pointer")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test13.xrefrelmissing.event.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "/x-gts-traits-schema/missingConstraintType",
                        },
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("reject trait pointer to non-string metadata")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test13.xrefrelnonstring.event.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "examples": ["not-a-constraint-type"],
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "/x-gts-traits-schema/examples",
                        },
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseOp13_TraitRef_ConstraintTypeMissing(HttpRunner):
    """§9.6 specific ref: the x-gts-ref CONSTRAINT type must itself exist.

    The topicRef value is a syntactically valid GTS id with the correct prefix,
    but neither the constraint type nor the value is registered. Validation MUST
    fail. Complements TestCaseOp13_TraitRef_TopicRefNonexistent, which registers
    the constraint type but leaves the referenced value unregistered.
    """

    config = Config(
        "OP#13 x-gts-ref: missing constraint type fails"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.xrefct.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.xrefct.topic.v1~",
                        },
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base whose x-gts-ref points at an unregistered topic type",
        ),
        _register_derived(
            "gts://gts.x.test13.xrefct.event.v1~x.test13._.leaf.v1~",
            "gts://gts.x.test13.xrefct.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.xrefct.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                },
            },
            "register derived with topicRef under the unregistered constraint type",
        ),
        _validate_type_schema(
            "gts.x.test13.xrefct.event.v1~",
            False,
            "validate should fail - x-gts-ref constraint type is not registered",
        ),
        _validate_type_schema(
            "gts.x.test13.xrefct.event.v1~x.test13._.leaf.v1~",
            False,
            "validate should fail - x-gts-ref constraint type is not registered",
        ),
    ]


class TestCaseOp13_TraitRef_RevalidationPreservesStoredSchema(HttpRunner):
    """A failed registration-with-validation must not remove committed state.

    The first request deliberately omits ``validate=true``, so the schema is
    accepted after syntax checks even though its concrete x-gts-ref target is
    not registered. A GET proves that registration committed the schema before
    an identical request with explicit validation fails. That later failure
    belongs only to the rejected request: the schema committed by the first
    request must remain retrievable unchanged.
    """

    config = Config(
        "OP#13 x-gts-ref: rejected identical revalidation preserves stored schema"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    schema = {
        "$$id": "gts://gts.x.test13.xrefpreserve.event.v1~",
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "topicRef": {
                "type": "string",
                "x-gts-ref": "gts.x.test13.xrefpreserve.topic.v1~",
            },
        },
    }
    teststeps = [
        # This request commits the schema. Without explicit validation, the
        # concrete target is checked for syntax but not registry existence.
        Step(
            RunRequest("register schema with an unregistered x-gts-ref target")
            .post("/entities")
            .with_json(schema)
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.id", "gts.x.test13.xrefpreserve.event.v1~")
            .assert_equal("body.is_type_schema", True)
        ),
        # Verify the first response represented a committed registration, not
        # merely a successful-looking response with no stored entity.
        Step(
            RunRequest("confirm unvalidated schema was committed")
            .get("/entities/gts.x.test13.xrefpreserve.event.v1~")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.id", "gts.x.test13.xrefpreserve.event.v1~")
            .assert_equal("body.content.type", "object")
            .assert_equal("body.content.properties.topicRef.type", "string")
        ),
        # The identical body is valid syntactically, but validate=true reaches
        # the existence check and rejects its missing constraint type.
        Step(
            RunRequest("reject identical schema when explicit validation checks its target")
            .post("/entities?validate=true")
            .with_json(schema)
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", True)
            .assert_contains(
                "body.error", "gts.x.test13.xrefpreserve.topic.v1~"
            )
        ),
        # Rejection of the second request must not undo the successful first
        # request. GET returning the original shape proves committed state was
        # preserved rather than merely returning a stale success envelope.
        Step(
            RunRequest("previously accepted schema remains registered")
            .get("/entities/gts.x.test13.xrefpreserve.event.v1~")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.id", "gts.x.test13.xrefpreserve.event.v1~")
            .assert_equal("body.content.type", "object")
            .assert_equal("body.content.properties.topicRef.type", "string")
        ),
    ]


class TestCaseOp13_TraitRef_ValidatedRegistrationFailureIsNotStored(HttpRunner):
    """A first-time registration rejected by validation must commit nothing."""

    config = Config(
        "OP#13 x-gts-ref: rejected validated registration is not stored"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    schema = {
        "$$id": "gts://gts.x.test13.xrefreject.event.v1~",
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "topicRef": {
                "type": "string",
                "x-gts-ref": "gts.x.test13.xrefreject.topic.v1~",
            },
        },
    }
    teststeps = [
        # This is registration and validation in one request. Because validation
        # fails, the registration must be atomic and commit no new entity.
        Step(
            RunRequest("reject first registration with an unregistered x-gts-ref target")
            .post("/entities?validate=true")
            .with_json(schema)
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", True)
            .assert_contains(
                "body.error", "gts.x.test13.xrefreject.topic.v1~"
            )
        ),
        # A missing entity is represented by the existing GET contract as HTTP
        # 200 with ok=false and null content, rather than by HTTP 404.
        Step(
            RunRequest("confirm rejected schema was never committed")
            .get("/entities/gts.x.test13.xrefreject.event.v1~")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.content", None)
            .assert_contains(
                "body.error", "gts.x.test13.xrefreject.event.v1~"
            )
        ),
    ]


class TestCaseOp13_TraitRef_InheritedChain_RootMissing(HttpRunner):
    """Inherited topicRef, case (a): the ref target's root/constraint type is missing.

    Chain: event base E (declares topicRef x-gts-ref = users root type) ->
    audit type A (sets topicRef to a deep users type, NOT validated) ->
    user type U (inherits A's topicRef, no own x-gts-traits). Validating U MUST
    fail because the referenced users type chain — starting at its root, which
    is also the x-gts-ref constraint type — is not registered at all.
    """

    config = Config(
        "OP#13 x-gts-ref inherited: root/constraint type missing fails"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # NOTE: the users type chain is intentionally NOT registered.
        _register(
            "gts://gts.x.test13.xrefia.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.xrefia.users.v1~",
                        },
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register event base with x-gts-ref to users root type",
        ),
        _register_derived(
            "gts://gts.x.test13.xrefia.event.v1~x.test13._.audit.v1~",
            "gts://gts.x.test13.xrefia.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.xrefia.users.v1~"
                        "x.test13._.tenant.v1~"
                        "x.test13._.admin.v1~"
                    ),
                },
            },
            "register audit type setting a deep topicRef (audit is not validated)",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.xrefia.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.user.v1~"
            ),
            "gts://gts.x.test13.xrefia.event.v1~x.test13._.audit.v1~",
            {"type": "object"},
            "register user type inheriting the audit topicRef (no own traits)",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.xrefia.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.user.v1~"
            ),
            False,
            "validate should fail - inherited topicRef root type does not exist",
        ),
    ]


class TestCaseOp13_TraitRef_InheritedChain_LeafMissing(HttpRunner):
    """Inherited topicRef, case (b): the ref target's leaf link is missing.

    The users root and an intermediate link are registered, but the deep leaf
    type used as the inherited topicRef value is NOT. Validating U MUST fail:
    every link of the referenced value's derivation chain must exist, not just
    its ancestors.
    """

    config = Config(
        "OP#13 x-gts-ref inherited: leaf link missing fails"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register the users root and ONE intermediate link, but not the leaf.
        _register(
            "gts://gts.x.test13.xrefib.users.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register users root type",
        ),
        _register_derived(
            "gts://gts.x.test13.xrefib.users.v1~x.test13._.tenant.v1~",
            "gts://gts.x.test13.xrefib.users.v1~",
            {"type": "object"},
            "register users intermediate type (tenant); leaf left unregistered",
        ),
        _register(
            "gts://gts.x.test13.xrefib.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.xrefib.users.v1~",
                        },
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register event base with x-gts-ref to users root type",
        ),
        _register_derived(
            "gts://gts.x.test13.xrefib.event.v1~x.test13._.audit.v1~",
            "gts://gts.x.test13.xrefib.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.xrefib.users.v1~"
                        "x.test13._.tenant.v1~"
                        "x.test13._.admin.v1~"
                    ),
                },
            },
            "register audit type setting a deep topicRef (audit is not validated)",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.xrefib.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.user.v1~"
            ),
            "gts://gts.x.test13.xrefib.event.v1~x.test13._.audit.v1~",
            {"type": "object"},
            "register user type inheriting the audit topicRef (no own traits)",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.xrefib.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.user.v1~"
            ),
            False,
            "validate should fail - inherited topicRef leaf type does not exist",
        ),
    ]


class TestCaseOp13_TraitRef_InheritedChain_FullyResolved(HttpRunner):
    """Inherited topicRef, case (c): the entire ref target chain exists.

    The users root, its intermediate link, and the deep leaf used as the
    inherited topicRef value are all registered. Validating U MUST pass. The
    referenced value carries two derivation segments beyond its root to show
    the chain-existence check applies at arbitrary depth.
    """

    config = Config(
        "OP#13 x-gts-ref inherited: full chain resolves"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register the full users type chain: root -> tenant -> admin (leaf).
        _register(
            "gts://gts.x.test13.xrefic.users.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register users root type",
        ),
        _register_derived(
            "gts://gts.x.test13.xrefic.users.v1~x.test13._.tenant.v1~",
            "gts://gts.x.test13.xrefic.users.v1~",
            {"type": "object"},
            "register users intermediate type (tenant)",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.xrefic.users.v1~"
                "x.test13._.tenant.v1~"
                "x.test13._.admin.v1~"
            ),
            "gts://gts.x.test13.xrefic.users.v1~x.test13._.tenant.v1~",
            {"type": "object"},
            "register users leaf type (admin) - the topicRef target",
        ),
        _register(
            "gts://gts.x.test13.xrefic.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": "gts.x.test13.xrefic.users.v1~",
                        },
                    },
                },
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register event base with x-gts-ref to users root type",
        ),
        _register_derived(
            "gts://gts.x.test13.xrefic.event.v1~x.test13._.audit.v1~",
            "gts://gts.x.test13.xrefic.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.test13.xrefic.users.v1~"
                        "x.test13._.tenant.v1~"
                        "x.test13._.admin.v1~"
                    ),
                },
            },
            "register audit type setting a deep topicRef (audit is not validated)",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.xrefic.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.user.v1~"
            ),
            "gts://gts.x.test13.xrefic.event.v1~x.test13._.audit.v1~",
            {"type": "object"},
            "register user type inheriting the audit topicRef (no own traits)",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.xrefic.event.v1~"
                "x.test13._.audit.v1~"
                "x.test13._.user.v1~"
            ),
            True,
            "validate should pass - inherited topicRef chain fully registered",
        ),
    ]


def _register_2020_trait_type(type_id, pair, label):
    """POST a Draft 2020-12 type whose x-gts-traits-schema uses prefixItems.

    The helpers register draft-07; this posts the entity directly so the type
    declares Draft 2020-12 and its trait schema exercises a post-Draft-07
    keyword (`prefixItems`).
    """
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json({
            "$$id": type_id,
            "$$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string"}},
            "x-gts-traits-schema": {
                "type": "object",
                "properties": {
                    "pair": {
                        "type": "array",
                        "prefixItems": [{"type": "string"}],
                    },
                },
            },
            "x-gts-traits": {"pair": pair},
        })
        .validate()
        .assert_equal("status_code", 200)
    )


class TestCaseOp13_TraitSchemaHonoursHostDialect_Rejects(HttpRunner):
    """OP#13 - the effective trait schema is validated under the host dialect.

    A Type Schema's trait schema MUST be interpreted under the dialect the type
    declares (README 11.0). A Draft 2020-12 trait schema using `prefixItems`
    that requires a string first item MUST reject a trait value whose first item
    is a number. An implementation that validates trait values under Draft-07
    would silently ignore `prefixItems` and wrongly accept it.
    """

    config = Config("OP#13 - trait schema honours host dialect (reject)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    type_id = "gts.x.test13.tdialect.bad.v1~"
    teststeps = [
        _register_2020_trait_type(
            "gts://gts.x.test13.tdialect.bad.v1~",
            [42],
            "register 2020-12 type with a non-conforming prefixItems trait value",
        ),
        _validate_type_schema(
            type_id,
            False,
            "prefixItems trait constraint must reject a number first item",
        ),
    ]


class TestCaseOp13_TraitSchemaHonoursHostDialect_Accepts(HttpRunner):
    """OP#13 - the same 2020-12 trait constraint accepts a conforming value."""

    config = Config("OP#13 - trait schema honours host dialect (accept)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    type_id = "gts.x.test13.tdialect.ok.v1~"
    teststeps = [
        _register_2020_trait_type(
            "gts://gts.x.test13.tdialect.ok.v1~",
            ["ok"],
            "register 2020-12 type with a conforming prefixItems trait value",
        ),
        _validate_type_schema(
            type_id,
            True,
            "prefixItems trait constraint must accept a string first item",
        ),
    ]
