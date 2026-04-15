"""x-gts-final / x-gts-abstract — comprehensive and interaction tests.

Tests for schema modifier keywords (section 9.11):
- x-gts-final: type cannot be inherited
- x-gts-abstract: type cannot be directly instantiated

These tests cover edge cases, boolean validation, schema-only enforcement,
and interactions with x-gts-traits (OP#13).
"""

from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    register as _register,
    register_derived as _register_derived,
    register_instance as _register_instance,
    validate_entity as _validate_entity,
    validate_instance as _validate_instance,
    validate_schema as _validate_schema,
)
from httprunner import HttpRunner, Config, Step, RunRequest


# ---------------------------------------------------------------------------
# x-gts-final tests
# ---------------------------------------------------------------------------


class TestCaseFinal_RejectDerivedSchema(HttpRunner):
    """x-gts-final: Derived schema from a final base MUST fail validation."""

    config = Config("final: reject derived schema").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.final.reject.v1~",
            {
                "type": "object",
                "x-gts-final": True,
                "properties": {"name": {"type": "string"}},
            },
            "register final base",
        ),
        _register_derived(
            "gts://gts.x.testfa.final.reject.v1~x.testfa._.derived.v1~",
            "gts://gts.x.testfa.final.reject.v1~",
            {"type": "object", "properties": {"extra": {"type": "string"}}},
            "register derived from final",
        ),
        _validate_schema(
            "gts.x.testfa.final.reject.v1~x.testfa._.derived.v1~",
            False,
            "validate derived should fail",
        ),
    ]


class TestCaseFinal_AllowWellKnownInstance(HttpRunner):
    """x-gts-final: Well-known instances of a final type MUST pass validation."""

    config = Config("final: allow well-known instance").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.final.inst.v1~",
            {
                "type": "object",
                "x-gts-final": True,
                "required": ["id", "description"],
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            "register final type",
        ),
        _register_instance(
            {
                "id": "gts.x.testfa.final.inst.v1~x.testfa._.running.v1",
                "description": "Running state",
            },
            "register well-known instance",
        ),
        _validate_instance(
            "gts.x.testfa.final.inst.v1~x.testfa._.running.v1",
            True,
            "validate well-known instance should pass",
        ),
    ]


class TestCaseFinal_AllowAnonymousInstance(HttpRunner):
    """x-gts-final: Anonymous instances of a final type MUST pass validation.

    Uses combined anonymous instance format: gts.type.v1~<UUID>
    """

    config = Config("final: allow anonymous instance").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.final.anon.v1~",
            {
                "type": "object",
                "x-gts-final": True,
                "required": ["id", "type", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register final type",
        ),
        _register_instance(
            {
                "id": "gts.x.testfa.final.anon.v1~b1c2d3e4-5678-4abc-8def-aabbccddeeff",
                "type": "gts.x.testfa.final.anon.v1~",
                "name": "Anonymous item",
            },
            "register combined anonymous instance",
        ),
        _validate_instance(
            "gts.x.testfa.final.anon.v1~b1c2d3e4-5678-4abc-8def-aabbccddeeff",
            True,
            "validate combined anonymous instance should pass",
        ),
    ]


class TestCaseFinal_MidChainFinal(HttpRunner):
    """x-gts-final: Mid-chain final blocks further derivation.

    Chain: A~ -> B~(final) -> C~. Validating C~ MUST fail.
    """

    config = Config("final: mid-chain final blocks derivation").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finalmid.base.v1~",
            {"type": "object", "properties": {"name": {"type": "string"}}},
            "register base A",
        ),
        _register_derived(
            "gts://gts.x.testfa.finalmid.base.v1~x.testfa._.mid.v1~",
            "gts://gts.x.testfa.finalmid.base.v1~",
            {"type": "object"},
            "register mid B (final)",
            top_level={"x-gts-final": True},
        ),
        _register_derived(
            "gts://gts.x.testfa.finalmid.base.v1~x.testfa._.mid.v1~x.testfa._.leaf.v1~",
            "gts://gts.x.testfa.finalmid.base.v1~x.testfa._.mid.v1~",
            {"type": "object", "properties": {"extra": {"type": "string"}}},
            "register leaf C from final B",
        ),
        _validate_schema(
            "gts.x.testfa.finalmid.base.v1~x.testfa._.mid.v1~x.testfa._.leaf.v1~",
            False,
            "validate C should fail - B is final",
        ),
    ]


class TestCaseFinal_SiblingUnaffected(HttpRunner):
    """x-gts-final: Sibling of a final type is unaffected.

    A~ -> B~(final) and A~ -> C~. C~ is valid because A~ is not final.
    """

    config = Config("final: sibling unaffected").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finalsib.base.v1~",
            {"type": "object", "properties": {"name": {"type": "string"}}},
            "register base A",
        ),
        _register_derived(
            "gts://gts.x.testfa.finalsib.base.v1~x.testfa._.final_b.v1~",
            "gts://gts.x.testfa.finalsib.base.v1~",
            {"type": "object"},
            "register B (final)",
            top_level={"x-gts-final": True},
        ),
        _register_derived(
            "gts://gts.x.testfa.finalsib.base.v1~x.testfa._.sibling_c.v1~",
            "gts://gts.x.testfa.finalsib.base.v1~",
            {"type": "object", "properties": {"extra": {"type": "string"}}},
            "register C (sibling) from A",
        ),
        _validate_schema(
            "gts.x.testfa.finalsib.base.v1~x.testfa._.sibling_c.v1~",
            True,
            "validate C should pass - A is not final",
        ),
    ]


class TestCaseFinal_FalseIsNoop(HttpRunner):
    """x-gts-final: false behaves the same as absent — derivation allowed."""

    config = Config("final: false is noop").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finalfalse.base.v1~",
            {
                "type": "object",
                "x-gts-final": False,
                "properties": {"name": {"type": "string"}},
            },
            "register base with final=false",
        ),
        _register_derived(
            "gts://gts.x.testfa.finalfalse.base.v1~x.testfa._.derived.v1~",
            "gts://gts.x.testfa.finalfalse.base.v1~",
            {"type": "object"},
            "register derived from final=false base",
        ),
        _validate_schema(
            "gts.x.testfa.finalfalse.base.v1~x.testfa._.derived.v1~",
            True,
            "validate derived should pass - final=false is noop",
        ),
    ]


class TestCaseFinal_NonBooleanRejected(HttpRunner):
    """x-gts-final: Non-boolean value MUST be rejected on registration.

    Registering a schema with x-gts-final: "yes" should fail.
    """

    config = Config("final: non-boolean rejected").base_url(get_gts_base_url())
    teststeps = [
        Step(
            RunRequest("register schema with final='yes' should be rejected")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testfa.finalbadval.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-final": "yes",
                "properties": {"name": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseFinal_InInstanceRejected(HttpRunner):
    """x-gts-final: Schema-only keyword in an instance MUST be rejected.

    An instance body containing x-gts-final should fail entity validation.
    """

    config = Config("final: in instance rejected").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finalininst.base.v1~",
            {
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register base schema",
        ),
        _register_instance(
            {
                "id": "gts.x.testfa.finalininst.base.v1~x.testfa._.item.v1",
                "x-gts-final": True,
            },
            "register instance with x-gts-final in body",
        ),
        _validate_entity(
            "gts.x.testfa.finalininst.base.v1~x.testfa._.item.v1",
            False,
            "validate-entity instance with schema keyword should fail",
            expected_entity_type="instance",
        ),
    ]


# ---------------------------------------------------------------------------
# x-gts-abstract tests
# ---------------------------------------------------------------------------


class TestCaseAbstract_RejectDirectInstance(HttpRunner):
    """x-gts-abstract: Direct instance of abstract type MUST fail validation."""

    config = Config("abstract: reject direct instance").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.abs.reject.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register abstract base",
        ),
        _register_instance(
            {
                "id": "gts.x.testfa.abs.reject.v1~x.testfa._.item.v1",
                "name": "Direct item",
            },
            "register instance of abstract type",
        ),
        _validate_instance(
            "gts.x.testfa.abs.reject.v1~x.testfa._.item.v1",
            False,
            "validate direct instance should fail",
            expected_id="gts.x.testfa.abs.reject.v1~x.testfa._.item.v1",
        ),
    ]


class TestCaseAbstract_AllowDerivedSchema(HttpRunner):
    """x-gts-abstract: Derived schema from abstract type MUST pass validation."""

    config = Config("abstract: allow derived schema").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.abs.derive.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "properties": {"name": {"type": "string"}},
            },
            "register abstract base",
        ),
        _register_derived(
            "gts://gts.x.testfa.abs.derive.v1~x.testfa._.concrete.v1~",
            "gts://gts.x.testfa.abs.derive.v1~",
            {"type": "object", "properties": {"extra": {"type": "string"}}},
            "register concrete derived",
        ),
        _validate_schema(
            "gts.x.testfa.abs.derive.v1~x.testfa._.concrete.v1~",
            True,
            "validate derived should pass",
        ),
    ]


class TestCaseAbstract_AllowInstanceOfConcreteDerived(HttpRunner):
    """x-gts-abstract: Instance of concrete derived type MUST pass.

    Abstract A~, concrete A~B~. Instance of B~ should pass.
    """

    config = Config("abstract: allow instance of concrete derived").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.abs.concinst.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register abstract base",
        ),
        _register_derived(
            "gts://gts.x.testfa.abs.concinst.v1~x.testfa._.concrete.v1~",
            "gts://gts.x.testfa.abs.concinst.v1~",
            {"type": "object", "properties": {"extra": {"type": "string"}}},
            "register concrete derived",
        ),
        _register_instance(
            {
                "id": "gts.x.testfa.abs.concinst.v1~x.testfa._.concrete.v1~x.testfa._.my_item.v1",
                "name": "My Item",
                "extra": "value",
            },
            "register instance of concrete derived",
        ),
        _validate_instance(
            "gts.x.testfa.abs.concinst.v1~x.testfa._.concrete.v1~x.testfa._.my_item.v1",
            True,
            "validate instance of concrete derived should pass",
        ),
    ]


class TestCaseAbstract_ChainOfAbstracts(HttpRunner):
    """x-gts-abstract: Chain of abstract types — only concrete leaf allows instances.

    Abstract A~, abstract A~B~, concrete A~B~C~.
    Instance of C~ passes. Instance of B~ fails.
    """

    config = Config("abstract: chain of abstracts").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.abs.chain.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register abstract A",
        ),
        _register_derived(
            "gts://gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~",
            "gts://gts.x.testfa.abs.chain.v1~",
            {"type": "object"},
            "register abstract B",
            top_level={"x-gts-abstract": True},
        ),
        _register_derived(
            "gts://gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~x.testfa._.leaf.v1~",
            "gts://gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~",
            {"type": "object", "properties": {"extra": {"type": "string"}}},
            "register concrete C",
        ),
        # Instance of concrete C — should pass
        _register_instance(
            {
                "id": "gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~x.testfa._.leaf.v1~x.testfa._.item.v1",
            },
            "register instance of C",
        ),
        _validate_instance(
            "gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~x.testfa._.leaf.v1~x.testfa._.item.v1",
            True,
            "validate instance of C should pass",
        ),
        # Instance of abstract B — should fail
        _register_instance(
            {
                "id": "gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~x.testfa._.item_b.v1",
            },
            "register instance of abstract B",
        ),
        _validate_instance(
            "gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~x.testfa._.item_b.v1",
            False,
            "validate instance of abstract B should fail",
            expected_id="gts.x.testfa.abs.chain.v1~x.testfa._.mid.v1~x.testfa._.item_b.v1",
        ),
    ]


class TestCaseAbstract_FalseIsNoop(HttpRunner):
    """x-gts-abstract: false behaves the same as absent — instances allowed."""

    config = Config("abstract: false is noop").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.absfalse.base.v1~",
            {
                "type": "object",
                "x-gts-abstract": False,
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base with abstract=false",
        ),
        _register_instance(
            {"id": "gts.x.testfa.absfalse.base.v1~x.testfa._.item.v1"},
            "register instance",
        ),
        _validate_instance(
            "gts.x.testfa.absfalse.base.v1~x.testfa._.item.v1",
            True,
            "validate instance should pass - abstract=false is noop",
        ),
    ]


class TestCaseAbstract_NonBooleanRejected(HttpRunner):
    """x-gts-abstract: Non-boolean value MUST be rejected on registration."""

    config = Config("abstract: non-boolean rejected").base_url(get_gts_base_url())
    teststeps = [
        Step(
            RunRequest("register schema with abstract=1 should be rejected")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testfa.absbadval.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-abstract": 1,
                "properties": {"name": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseAbstract_InInstanceRejected(HttpRunner):
    """x-gts-abstract: Schema-only keyword in an instance MUST be rejected."""

    config = Config("abstract: in instance rejected").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.absininst.base.v1~",
            {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base schema",
        ),
        _register_instance(
            {
                "id": "gts.x.testfa.absininst.base.v1~x.testfa._.item.v1",
                "x-gts-abstract": True,
            },
            "register instance with x-gts-abstract",
        ),
        _validate_entity(
            "gts.x.testfa.absininst.base.v1~x.testfa._.item.v1",
            False,
            "validate-entity instance with schema keyword should fail",
            expected_entity_type="instance",
        ),
    ]


class TestCaseAbstract_CombinedAnonInstanceRejected(HttpRunner):
    """x-gts-abstract: Combined anonymous instance of abstract type MUST fail."""

    config = Config("abstract: combined anon instance rejected").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.absanon.base.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "required": ["id", "type"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                },
            },
            "register abstract type",
        ),
        _register_instance(
            {
                "id": "gts.x.testfa.absanon.base.v1~c1d2e3f4-5678-4abc-8def-aabbccddeeff",
                "type": "gts.x.testfa.absanon.base.v1~",
            },
            "register combined anonymous instance of abstract type",
        ),
        _validate_instance(
            "gts.x.testfa.absanon.base.v1~c1d2e3f4-5678-4abc-8def-aabbccddeeff",
            False,
            "validate combined anon instance of abstract should fail",
            expected_id="gts.x.testfa.absanon.base.v1~c1d2e3f4-5678-4abc-8def-aabbccddeeff",
        ),
    ]


# ---------------------------------------------------------------------------
# Registration guard tests (?validate=true)
# ---------------------------------------------------------------------------


class TestCaseFinal_RegistrationGuardRejectsDerived(HttpRunner):
    """x-gts-final: Registration with ?validate=true MUST reject derived from final base."""

    config = Config("final: registration guard rejects derived").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finalreg.base.v1~",
            {
                "type": "object",
                "x-gts-final": True,
                "properties": {"name": {"type": "string"}},
            },
            "register final base",
        ),
        Step(
            RunRequest("register derived from final with validate=true should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testfa.finalreg.base.v1~x.testfa._.derived.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testfa.finalreg.base.v1~"},
                    {"type": "object", "properties": {"extra": {"type": "string"}}},
                ],
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseAbstract_RegistrationGuardRejectsInstance(HttpRunner):
    """x-gts-abstract: Registration with ?validate=true MUST reject instance of abstract type."""

    config = Config("abstract: registration guard rejects instance").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.absreg.base.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register abstract base",
        ),
        Step(
            RunRequest("register instance of abstract with validate=true should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "id": "gts.x.testfa.absreg.base.v1~x.testfa._.item.v1",
                "name": "Direct item",
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


# ---------------------------------------------------------------------------
# Keyword placement tests
# ---------------------------------------------------------------------------


class TestCaseFinal_InsideAllOfRejected(HttpRunner):
    """x-gts-final inside allOf MUST be rejected — keyword must be at top level.

    The keyword is placed inside an allOf entry instead of at the schema
    top level. Registration with validation should reject this.
    """

    config = Config("final: inside allOf rejected").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finalallof.base.v1~",
            {"type": "object", "properties": {"name": {"type": "string"}}},
            "register base schema",
        ),
        Step(
            RunRequest("register derived with x-gts-final inside allOf should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testfa.finalallof.base.v1~x.testfa._.derived.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testfa.finalallof.base.v1~"},
                    {
                        "type": "object",
                        "x-gts-final": True,
                        "properties": {"extra": {"type": "string"}},
                    },
                ],
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseAbstract_InsideAllOfRejected(HttpRunner):
    """x-gts-abstract inside allOf MUST be rejected — keyword must be at top level."""

    config = Config("abstract: inside allOf rejected").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.absallof.base.v1~",
            {"type": "object", "properties": {"name": {"type": "string"}}},
            "register base schema",
        ),
        Step(
            RunRequest("register derived with x-gts-abstract inside allOf should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testfa.absallof.base.v1~x.testfa._.derived.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testfa.absallof.base.v1~"},
                    {
                        "type": "object",
                        "x-gts-abstract": True,
                        "properties": {"extra": {"type": "string"}},
                    },
                ],
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


# ---------------------------------------------------------------------------
# Interaction tests
# ---------------------------------------------------------------------------


class TestCaseInteraction_BothModifiersRejected(HttpRunner):
    """Both x-gts-final and x-gts-abstract on same schema MUST be rejected on registration."""

    config = Config("interaction: both modifiers rejected").base_url(get_gts_base_url())
    teststeps = [
        Step(
            RunRequest("register schema with both modifiers should be rejected")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testfa.both.invalid.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-final": True,
                "x-gts-abstract": True,
                "properties": {"name": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseInteraction_FinalWithTraitsFullyResolved(HttpRunner):
    """Final type with all traits resolved — validation passes.

    Since a final type cannot be derived from, all required traits
    MUST be fully resolved on the final type itself.
    """

    config = Config("interaction: final with traits fully resolved").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finaltrait.base.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "retention": {"type": "string", "default": "P30D"},
                        "priority": {"type": "integer"},
                    },
                    "required": ["priority"],
                },
                "properties": {"name": {"type": "string"}},
            },
            "register base with trait schema",
        ),
        _register_derived(
            "gts://gts.x.testfa.finaltrait.base.v1~x.testfa._.leaf.v1~",
            "gts://gts.x.testfa.finaltrait.base.v1~",
            {
                "type": "object",
                "x-gts-traits": {
                    "priority": 5,
                },
            },
            "register final derived with traits resolved",
            top_level={"x-gts-final": True},
        ),
        _validate_schema(
            "gts.x.testfa.finaltrait.base.v1~x.testfa._.leaf.v1~",
            True,
            "validate final with resolved traits should pass",
        ),
    ]


class TestCaseInteraction_FinalWithTraitsMissing(HttpRunner):
    """Final type with unresolved required traits — validation fails.

    A final type cannot delegate trait resolution to descendants,
    so all required traits without defaults MUST be provided.
    """

    config = Config("interaction: final with missing traits").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.finalmiss.base.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "integer"},
                    },
                    "required": ["priority"],
                },
                "properties": {"name": {"type": "string"}},
            },
            "register base with required trait (no default)",
        ),
        _register_derived(
            "gts://gts.x.testfa.finalmiss.base.v1~x.testfa._.leaf.v1~",
            "gts://gts.x.testfa.finalmiss.base.v1~",
            {
                "type": "object",
                # x-gts-traits intentionally omitted — priority not resolved
            },
            "register final derived without resolving traits",
            top_level={"x-gts-final": True},
        ),
        _validate_schema(
            "gts.x.testfa.finalmiss.base.v1~x.testfa._.leaf.v1~",
            False,
            "validate final with missing required traits should fail",
        ),
    ]


class TestCaseInteraction_AbstractWithIncompleteTraitsOk(HttpRunner):
    """Abstract type with unresolved traits — validation passes.

    Abstract types are not leaf schemas, so trait resolution completeness
    is not enforced on them.
    """

    config = Config("interaction: abstract with incomplete traits ok").base_url(get_gts_base_url())
    teststeps = [
        _register(
            "gts://gts.x.testfa.abstrait.base.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "x-gts-traits-schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "priority": {"type": "integer"},
                    },
                    "required": ["priority"],
                },
                "properties": {"name": {"type": "string"}},
            },
            "register abstract base with required trait (no default)",
        ),
        _validate_schema(
            "gts.x.testfa.abstrait.base.v1~",
            True,
            "validate abstract with incomplete traits should pass",
        ),
    ]


class TestCaseInteraction_AbstractBaseFinalDerived(HttpRunner):
    """Abstract base + final derived: the complete lifecycle.

    Abstract A~ (no instances), final A~B~ (instances, no further derivation).
    B has instances, B has no derived, A has no direct instances.
    """

    config = Config("interaction: abstract base + final derived").base_url(get_gts_base_url())
    teststeps = [
        # Register abstract base
        _register(
            "gts://gts.x.testfa.absfinal.base.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register abstract base A",
        ),
        # Register concrete + final derived
        _register_derived(
            "gts://gts.x.testfa.absfinal.base.v1~x.testfa._.concrete.v1~",
            "gts://gts.x.testfa.absfinal.base.v1~",
            {
                "type": "object",
                "properties": {"extra": {"type": "string"}},
            },
            "register concrete final derived B",
            top_level={"x-gts-final": True},
        ),
        # B is valid as a schema
        _validate_schema(
            "gts.x.testfa.absfinal.base.v1~x.testfa._.concrete.v1~",
            True,
            "validate B should pass",
        ),
        # Instance of B — should pass (B is concrete)
        _register_instance(
            {
                "id": "gts.x.testfa.absfinal.base.v1~x.testfa._.concrete.v1~x.testfa._.item.v1",
                "name": "My Item",
                "extra": "value",
            },
            "register instance of B",
        ),
        _validate_instance(
            "gts.x.testfa.absfinal.base.v1~x.testfa._.concrete.v1~x.testfa._.item.v1",
            True,
            "validate instance of B should pass",
        ),
        # Derived from B — should fail (B is final)
        _register_derived(
            "gts://gts.x.testfa.absfinal.base.v1~x.testfa._.concrete.v1~x.testfa._.sub.v1~",
            "gts://gts.x.testfa.absfinal.base.v1~x.testfa._.concrete.v1~",
            {"type": "object"},
            "attempt to derive from final B",
        ),
        _validate_schema(
            "gts.x.testfa.absfinal.base.v1~x.testfa._.concrete.v1~x.testfa._.sub.v1~",
            False,
            "validate derived from final B should fail",
        ),
        # Direct instance of A — should fail (A is abstract)
        _register_instance(
            {
                "id": "gts.x.testfa.absfinal.base.v1~x.testfa._.direct.v1",
                "name": "Direct from abstract",
            },
            "register direct instance of abstract A",
        ),
        _validate_instance(
            "gts.x.testfa.absfinal.base.v1~x.testfa._.direct.v1",
            False,
            "validate direct instance of abstract A should fail",
            expected_id="gts.x.testfa.absfinal.base.v1~x.testfa._.direct.v1",
        ),
    ]


if __name__ == "__main__":
    TestCaseFinal_RejectDerivedSchema().test_start()
