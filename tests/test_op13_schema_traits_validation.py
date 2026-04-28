from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    register as _register,
    register_derived as _register_derived,
    validate_entity as _validate_entity,
    validate_type_schema as _validate_type_schema,
)
from httprunner import HttpRunner, Config


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
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
                        "gts.x.core.events.topic.v1~"
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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
                            "default": (
                                "gts.x.core.events.topic.v1~"
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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
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
            "register base with one trait without default",
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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
                            "default": (
                                "gts.x.core.events.topic.v1~"
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
                        "gts.x.core.events.topic.v1~"
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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
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
                        "gts.x.core.events.topic.v1~"
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
                },
            },
            "register mid-level adding priority trait (no default)",
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


class TestCaseOp13_TraitsInvalid_OverrideInChain(HttpRunner):
    """OP#13 - Traits: descendant cannot override ancestor trait value."""
    config = Config("OP#13 - Override In Chain").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.ovr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {
                            "type": "string",
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
            "gts://gts.x.test13.ovr.event.v1~x.test13._.mid_ovr.v1~",
            "gts://gts.x.test13.ovr.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P30D",
                },
            },
            "register mid-level setting retention=P30D",
        ),
        _validate_type_schema(
            "gts.x.test13.ovr.event.v1~x.test13._.mid_ovr.v1~",
            True,
            "validate mid-level",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.ovr.event.v1~"
                "x.test13._.mid_ovr.v1~"
                "x.test13._.leaf_ovr.v1~"
            ),
            "gts://gts.x.test13.ovr.event.v1~x.test13._.mid_ovr.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P365D",
                },
            },
            "register leaf overriding retention=P365D",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.ovr.event.v1~"
                "x.test13._.mid_ovr.v1~"
                "x.test13._.leaf_ovr.v1~"
            ),
            False,
            "validate should fail - trait override not allowed",
        ),
    ]


class TestCaseOp13_TraitsInvalid_OverrideTopicRef3Level(HttpRunner):
    """OP#13 - Traits: 3-level chain, leaf overrides topicRef.

    Mid-level sets topicRef to audit topic, leaf tries notification
    topic. Validation must fail (immutable-once-set).
    """
    config = Config(
        "OP#13 - Override TopicRef 3-Level"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.ovt.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {
                            "type": "string",
                            "x-gts-ref": (
                                "gts.x.core.events.topic.v1~"
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
            "register base with topicRef + retention traits",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.ovt.event.v1~"
                "x.test13._.audit_evt.v1~"
            ),
            "gts://gts.x.test13.ovt.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.core.events.topic.v1~"
                        "x.core._.audit.v1"
                    ),
                },
            },
            "register mid-level setting topicRef=audit",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.ovt.event.v1~"
                "x.test13._.audit_evt.v1~"
            ),
            True,
            "validate mid-level - topicRef set",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.ovt.event.v1~"
                "x.test13._.audit_evt.v1~"
                "x.test13._.most_derived.v1~"
            ),
            (
                "gts://gts.x.test13.ovt.event.v1~"
                "x.test13._.audit_evt.v1~"
            ),
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.core.events.topic.v1~"
                        "x.core._.notification.v1"
                    ),
                },
            },
            "register leaf overriding topicRef=notification",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.ovt.event.v1~"
                "x.test13._.audit_evt.v1~"
                "x.test13._.most_derived.v1~"
            ),
            False,
            "validate should fail - topicRef override not allowed",
        ),
    ]


class TestCaseOp13_TraitsInvalid_ChangeDefaultInMid(HttpRunner):
    """OP#13 - Traits: mid-level changes default set by base.

    Base sets retention default=P30D. Mid-level redeclares
    retention default=P90D. Validation must fail - defaults
    set by ancestor are immutable.
    """
    config = Config(
        "OP#13 - Change Default In Mid-Level"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.chdfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {
                            "type": "string",
                            "default": "P30D",
                        },
                        "topicRef": {
                            "type": "string",
                        },
                    },
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
                "gts://gts.x.test13.chdfl.event.v1~"
                "x.test13._.chdfl_mid.v1~"
            ),
            "gts://gts.x.test13.chdfl.event.v1~",
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
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.core.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                },
            },
            "register mid changing retention default to P90D",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.chdfl.event.v1~"
                "x.test13._.chdfl_mid.v1~"
            ),
            False,
            "validate should fail - default override not allowed",
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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
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
                        "gts.x.core.events.topic.v1~"
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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
                        },
                        "retention": {
                            "type": "string",
                        },
                    },
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base (no defaults)",
        ),
        _register_derived(
            "gts://gts.x.test13.entm.event.v1~x.test13._.bad_ent.v1~",
            "gts://gts.x.test13.entm.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "topicRef": (
                        "gts.x.core.events.topic.v1~"
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
                        "x-gts-ref": "gts.x.core.events.topic.v1~",
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
                        "gts.x.core.events.topic.v1~"
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
            "gts://gts.x.test13.traits.retention.v1~",
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
            "gts://gts.x.test13.traits.topic.v1~",
            {
                "type": "object",
                "properties": {
                    "topicRef": {
                        "description": "Topic reference.",
                        "type": "string",
                        "x-gts-ref": (
                            "gts.x.core.events.topic.v1~"
                        ),
                    },
                },
            },
            "register standalone TopicTrait schema",
        ),
        _register(
            "gts://gts.x.test13.refm.event.v1~",
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
        # Derived only provides retention, missing topicRef
        _register_derived(
            (
                "gts://gts.x.test13.refm.event.v1~"
                "x.test13._.ref_incomplete.v1~"
            ),
            "gts://gts.x.test13.refm.event.v1~",
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
                "gts.x.test13.refm.event.v1~"
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
    """OP#13 - Traits: base additionalProperties=false blocks extension."""
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
                            "x-gts-ref": "gts.x.core.events.topic.v1~",
                        },
                    },
                },
                "x-gts-traits": {
                    "retention": "P30D",
                    "topicRef": (
                        "gts.x.core.events.topic.v1~"
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
    """OP#13 - Traits: x-gts-traits-schema refs itself."""
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
                "properties": {
                    "retention": {
                        "type": "string",
                    },
                },
            },
            "register standalone trait schema",
        ),
        _register(
            "gts://gts.x.test13.cyc.selfevt.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "allOf": [
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".cyc.selfref.v1~"
                            ),
                        },
                        {
                            "$$ref": (
                                "gts://gts.x.test13"
                                ".cyc.selfref.v1~"
                            ),
                        },
                    ],
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with self-cycling trait ref",
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
            (
                "gts.x.test13.cyc.selfevt.v1~"
                "x.test13._.cyc_self_leaf.v1~"
            ),
            False,
            "validate should fail - cycling ref in traits-schema",
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
                            "gts.x.core.events.topic.v1~"
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
                        "gts.x.core.events.topic.v1~"
                        "x.test13._.orders.v1"
                    ),
                },
            },
            "register derived with traits",
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

class TestCaseOp13_TraitsInvalid_TraitsSchemaNotObject(HttpRunner):
    """OP#13 - Traits: x-gts-traits-schema with type=integer.

    Must fail - trait schema must have type=object.
    """
    config = Config(
        "OP#13 - Traits Schema Not Object"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.tsnobj.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "integer",
                },
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base with type=integer trait schema",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.tsnobj.event.v1~"
                "x.test13._.tsnobj_leaf.v1~"
            ),
            "gts://gts.x.test13.tsnobj.event.v1~",
            {
                "type": "object",
            },
            "register derived",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.tsnobj.event.v1~"
                "x.test13._.tsnobj_leaf.v1~"
            ),
            False,
            "validate should fail - trait schema type is integer",
        ),
    ]


class TestCaseOp13_TraitsInvalid_TraitsInInstance(HttpRunner):
    """OP#13 - Traits: x-gts-traits in an instance document.

    Trait keywords are schema-only. Instance with x-gts-traits
    must fail entity validation.
    """
    config = Config(
        "OP#13 - Traits In Instance"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.tinst.event.v1~",
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
            "register base schema with traits",
        ),
        _register_derived(
            (
                "gts://gts.x.test13.tinst.event.v1~"
                "x.test13._.tinst_leaf.v1~"
            ),
            "gts://gts.x.test13.tinst.event.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "retention": "P90D",
                },
            },
            "register derived with traits",
        ),
        _validate_type_schema(
            (
                "gts.x.test13.tinst.event.v1~"
                "x.test13._.tinst_leaf.v1~"
            ),
            True,
            "validate derived schema - ok",
        ),
        _validate_entity(
            (
                "gts.x.test13.tinst.event.v1~"
                "x.test13._.tinst_leaf.v1~"
            ),
            False,
            "validate entity should fail - traits in instance",
        ),
    ]


class TestCaseOp13_TraitsInvalid_TraitsSchemaInInstance(HttpRunner):
    """OP#13 - Traits: x-gts-traits-schema in an instance document.

    Trait keywords are schema-only. Instance with
    x-gts-traits-schema must fail entity validation.
    """
    config = Config(
        "OP#13 - Traits Schema In Instance"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.tsinst.event.v1~",
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
            "register base schema with traits-schema",
        ),
        _validate_entity(
            "gts.x.test13.tsinst.event.v1~",
            False,
            "validate entity should fail - traits-schema in instance",
        ),
    ]
