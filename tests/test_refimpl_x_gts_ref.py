"""Tests for x-gts-type-ref / x-gts-instance-ref on concrete schemas.

Each field uses the keyword matching the kind of its candidates. These cases
cover combinator traversal, local references, arrays, and registry modes. §10
matching itself (minor versions, segment and UUID boundaries) is covered by
the shared test cases in test_x_gts_entity_ref.py; operand validity, candidate
kind, selected-leaf `/$id`, and the removed `x-gts-ref` keyword are covered
there too.
"""

import pytest

from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    validate_instance as _validate_instance,
    validate_type_schema as _validate_type_schema,
)
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseXGtsRef_PrefixAndSelfRef(HttpRunner):
    """entity reference: prefix enforcement and /$id self-reference."""
    config = Config("entity reference: prefix and self-ref").base_url(get_gts_base_url())

    def test_start(self):
        """Run entity reference prefix and self-reference test steps."""
        super().test_start()

    teststeps = [
        # Register a capability base type (not used directly here, acts as prefix root)
        Step(
            RunRequest("register capability base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref._.capability.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "description"],
                "properties": {
                    "id": {"type": "string", "x-gts-instance-ref": "/$$id"},
                    "description": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Reigster a test capability
        Step(
            RunRequest("register capability base schema")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref._.capability.v1~x.vendor._.has_ws.v1",
                "description": "Has WebSocket",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Try to reigster a capability with wrong base type
        Step(
            RunRequest("register capability base schema")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref._.wrong_capability.v1~x.vendor._.has_ws.v1",
                "description": "Has WebSocket",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate wrong capability - should fail because it does not match the base type
        Step(
            RunRequest("validate wrong capability")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref._.wrong_capability.v1~x.vendor._.has_ws.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        # Register a module schema that references capability IDs by prefix and enforces /$id on its own type field
        Step(
            RunRequest("register module schema with entity reference prefix and self-ref")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref._.module.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["type", "id", "capabilities"],
                "properties": {
                    "type": {"type": "string", "x-gts-type-ref": "/$$id"},
                    "id": {"type": "string"},
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string", "x-gts-instance-ref": "gts.x.testref._.capability.v1~"},
                        "minItems": 0,
                        "uniqueItems": True
                    }
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register a valid module instance
        Step(
            RunRequest("register valid module instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.testref._.module.v1~",
                "id": "gts.x.testref._.module.v1~x.vendor._.chat.v1",
                "capabilities": [
                    "gts.x.testref._.capability.v1~x.vendor._.has_ws.v1",
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate valid instance
        Step(
            RunRequest("validate valid module instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref._.module.v1~x.vendor._.chat.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Register an invalid module instance (wrong capability prefix)
        Step(
            RunRequest("register invalid module instance - wrong capability prefix")
            .post("/entities")
            .with_json({
                "type": "gts.x.testref._.module.v1~",
                "id": "gts.x.testref._.module.v1~x.vendor._.chat2.v1",
                "capabilities": [
                    "gts.y.other._.capability.v1~x.vendor._.foo.v1"  # wrong prefix
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate invalid instance (should fail)
        Step(
            RunRequest("validate invalid module instance - wrong capability prefix should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref._.module.v1~x.vendor._.chat2.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        # Register another invalid module instance (type mismatch vs ./$/id)
        Step(
            RunRequest("register invalid module instance - type mismatch")
            .post("/entities")
            .with_json({
                "type": "gts.x.testref._.wrong.v1~",  # does not equal $$id
                "id": "gts.x.testref._.module.v1~x.vendor._.chat3.v1",
                "capabilities": []
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate invalid module instance - type mismatch should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref._.module.v1~x.vendor._.chat3.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_OneOf(HttpRunner):
    """x-gts-instance-ref: oneOf combinator - exactly one branch must match"""
    config = Config("x-gts-instance-ref: oneOf combinator").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-instance-ref oneOf combinator test steps."""
        super().test_start()

    teststeps = [
        # Register two target schemas
        Step(
            RunRequest("register target_a schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_a.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_b.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register instances of each target
        Step(
            RunRequest("register target_a instance")
            .post("/entities")
            .with_json({
                "kind": "a",
                "id": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b instance")
            .post("/entities")
            .with_json({
                "kind": "b",
                "id": "gts.x.testref_comb._.target_b.v1~x.vendor._.b1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register "other" schema + instance for negative test
        Step(
            RunRequest("register other schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.other.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register other instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_comb._.other.v1~x.vendor._.o1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register oneOf schema: ref must match exactly one of target_a or target_b
        Step(
            RunRequest("register oneOf schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.oneof_ref.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "oneOf": [
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_a.v1~"},
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_b.v1~"},
                        ]
                    }
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Valid instance matching first branch
        Step(
            RunRequest("register valid oneOf instance - first branch")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
                "id": "gts.x.testref_comb._.oneof_ref.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate oneOf instance - first branch should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.oneof_ref.v1~x.vendor._.i1.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Valid instance matching second branch
        Step(
            RunRequest("register valid oneOf instance - second branch")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.target_b.v1~x.vendor._.b1.v1.0",
                "id": "gts.x.testref_comb._.oneof_ref.v1~x.vendor._.i2.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate oneOf instance - second branch should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.oneof_ref.v1~x.vendor._.i2.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Invalid instance matching neither branch
        Step(
            RunRequest("register invalid oneOf instance - no branch matches")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.other.v1~x.vendor._.o1.v1.0",
                "id": "gts.x.testref_comb._.oneof_ref.v1~x.vendor._.i3.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate oneOf instance - no branch matches should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.oneof_ref.v1~x.vendor._.i3.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        # Overlapping patterns: register schema where both branches match
        Step(
            RunRequest("register oneOf schema with overlapping patterns")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.oneof_overlap.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "oneOf": [
                            {"x-gts-instance-ref": "gts.x.testref_comb.*"},
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_a.v1~"},
                        ]
                    }
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register instance matching both overlapping branches")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
                "id": "gts.x.testref_comb._.oneof_overlap.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate overlapping oneOf instance - both match should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.oneof_overlap.v1~x.vendor._.i1.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_OneOfSharedStructuralKeywords(HttpRunner):
    """x-gts-instance-ref: oneOf branches that share structural keywords and differ only
    by x-gts-instance-ref must still validate.

    The JSON Schema engine does not see x-gts-instance-ref (its exclusivity is enforced
    separately). Branches like ``{"type":"string","x-gts-instance-ref":"...a~"}`` and
    ``{"type":"string","x-gts-instance-ref":"...b~"}`` are structurally identical once
    x-gts-instance-ref is set aside, so an implementation that hands the raw oneOf to a
    structural validator sees *every* string match *both* branches and rejects
    every value. A reference to a valid target must pass.
    """

    config = Config("x-gts-instance-ref: oneOf shared structural keywords").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register target_a schema (shared-kw)")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_shared._.target_a.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b schema (shared-kw)")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_shared._.target_b.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_a instance (shared-kw)")
            .post("/entities")
            .with_json({"id": "gts.x.testref_shared._.target_a.v1~x.vendor._.a1.v1.0"})
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b instance (shared-kw)")
            .post("/entities")
            .with_json({"id": "gts.x.testref_shared._.target_b.v1~x.vendor._.b1.v1.0"})
            .validate()
            .assert_equal("status_code", 200)
        ),
        # oneOf branches share `type: string` and differ only by x-gts-instance-ref.
        Step(
            RunRequest("register oneOf schema with shared structural keywords")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_shared._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "oneOf": [
                            {"type": "string", "x-gts-instance-ref": "gts.x.testref_shared._.target_a.v1~"},
                            {"type": "string", "x-gts-instance-ref": "gts.x.testref_shared._.target_b.v1~"},
                        ],
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Reference to a valid target_a instance -> matches exactly one branch.
        Step(
            RunRequest("register holder instance referencing target_a")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_shared._.target_a.v1~x.vendor._.a1.v1.0",
                "id": "gts.x.testref_shared._.holder.v1~x.vendor._.h1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_shared._.holder.v1~x.vendor._.h1.v1.0",
            True,
            "oneOf with shared structural keywords must accept a valid target",
        ),
        # Reference to a valid target_b instance -> matches the other branch.
        Step(
            RunRequest("register holder instance referencing target_b")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_shared._.target_b.v1~x.vendor._.b1.v1.0",
                "id": "gts.x.testref_shared._.holder.v1~x.vendor._.h2.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_shared._.holder.v1~x.vendor._.h2.v1.0",
            True,
            "oneOf with shared structural keywords must accept the other target",
        ),
    ]


class TestCaseXGtsRef_AnyOf(HttpRunner):
    """x-gts-instance-ref: anyOf combinator - at least one branch must match"""
    config = Config("x-gts-instance-ref: anyOf combinator").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-instance-ref anyOf combinator test steps."""
        super().test_start()

    teststeps = [
        # Register shared target schemas and instances
        Step(
            RunRequest("register target_a schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_a.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_b.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_a instance")
            .post("/entities")
            .with_json({
                "kind": "a",
                "id": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b instance")
            .post("/entities")
            .with_json({
                "kind": "b",
                "id": "gts.x.testref_comb._.target_b.v1~x.vendor._.b1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register other schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.other.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register other instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_comb._.other.v1~x.vendor._.o1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register anyOf schema
        Step(
            RunRequest("register anyOf schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.anyof_ref.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "anyOf": [
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_a.v1~"},
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_b.v1~"},
                        ]
                    }
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Valid instance matching one branch
        Step(
            RunRequest("register valid anyOf instance")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
                "id": "gts.x.testref_comb._.anyof_ref.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate anyOf instance - should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.anyof_ref.v1~x.vendor._.i1.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Invalid instance matching no branch
        Step(
            RunRequest("register invalid anyOf instance")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.other.v1~x.vendor._.o1.v1.0",
                "id": "gts.x.testref_comb._.anyof_ref.v1~x.vendor._.i2.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate anyOf instance - no branch matches should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.anyof_ref.v1~x.vendor._.i2.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_AllOf(HttpRunner):
    """x-gts-instance-ref: allOf combinator - all branches must match"""
    config = Config("x-gts-instance-ref: allOf combinator").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-instance-ref allOf combinator test steps."""
        super().test_start()

    teststeps = [
        # Register shared target schemas and instances
        Step(
            RunRequest("register target_a schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_a.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_b.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_a instance")
            .post("/entities")
            .with_json({
                "kind": "a",
                "id": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register allOf schema with single branch
        Step(
            RunRequest("register allOf schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.allof_ref.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "allOf": [
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_a.v1~"},
                        ]
                    }
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Valid instance matching the branch
        Step(
            RunRequest("register valid allOf instance")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
                "id": "gts.x.testref_comb._.allof_ref.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate allOf instance - should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.allof_ref.v1~x.vendor._.i1.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Intentionally unsatisfiable: requires ref to match both target_a AND target_b
        # prefixes simultaneously, which is impossible for a single GTS ID.
        # Tests that allOf correctly rejects when not all branches can be satisfied.
        Step(
            RunRequest("register strict allOf schema - two incompatible branches")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.allof_strict.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "allOf": [
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_a.v1~"},
                            {"x-gts-instance-ref": "gts.x.testref_comb._.target_b.v1~"},
                        ]
                    }
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Instance matches target_a but not target_b — allOf requires both
        Step(
            RunRequest("register invalid allOf instance - one branch fails")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.target_a.v1~x.vendor._.a1.v1.0",
                "id": "gts.x.testref_comb._.allof_strict.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate allOf instance - one branch fails should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.allof_strict.v1~x.vendor._.i1.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_NestedCombinators(HttpRunner):
    """x-gts-instance-ref: nested combinators - allOf wrapping oneOf"""
    config = Config("x-gts-instance-ref: nested combinators").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-instance-ref nested combinator test steps."""
        super().test_start()

    teststeps = [
        # Register shared target schemas and instances
        Step(
            RunRequest("register target_a schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_a.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.target_b.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register target_b instance")
            .post("/entities")
            .with_json({
                "kind": "b",
                "id": "gts.x.testref_comb._.target_b.v1~x.vendor._.b1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register other schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.other.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register other instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_comb._.other.v1~x.vendor._.o1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register schema with allOf wrapping oneOf
        Step(
            RunRequest("register nested combinator schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_comb._.nested.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "allOf": [
                            {
                                "oneOf": [
                                    {"x-gts-instance-ref": "gts.x.testref_comb._.target_a.v1~"},
                                    {"x-gts-instance-ref": "gts.x.testref_comb._.target_b.v1~"},
                                ]
                            }
                        ]
                    }
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Valid instance - matches one oneOf branch
        Step(
            RunRequest("register valid nested combinator instance")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.target_b.v1~x.vendor._.b1.v1.0",
                "id": "gts.x.testref_comb._.nested.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate nested combinator instance - should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.nested.v1~x.vendor._.i1.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Invalid instance - matches no oneOf branch
        Step(
            RunRequest("register invalid nested combinator instance")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_comb._.other.v1~x.vendor._.o1.v1.0",
                "id": "gts.x.testref_comb._.nested.v1~x.vendor._.i2.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate nested combinator instance - no match should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_comb._.nested.v1~x.vendor._.i2.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_ImplicitObjectAndLocalRef(HttpRunner):
    config = Config("x-gts-instance-ref: implicit object and local refs").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register implicit object target schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_implicit._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register implicit object x-gts-instance-ref schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_implicit._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "required": ["id", "ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_implicit._.target.v1~",
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register implicit object invalid reference")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_implicit._.holder.v1~x.vendor._.bad.v1",
                "ref": "gts.x.other._.target.v1~x.vendor._.bad.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate implicit object invalid reference")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_implicit._.holder.v1~x.vendor._.bad.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "does not match pattern")
        ),
        _validate_type_schema(
            "gts.x.testref_implicit._.holder.v1~",
            True,
            "validate implicit object holder schema",
        ),
        Step(
            RunRequest("register local ref target schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_local._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register local ref x-gts-instance-ref schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_local._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {"$$ref": "#/definitions/TargetRef"},
                },
                "definitions": {
                    "TargetRef": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_local._.target.v1~",
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register local ref invalid reference")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_local._.holder.v1~x.vendor._.bad.v1",
                "ref": "gts.x.other._.target.v1~x.vendor._.bad.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate local ref invalid reference")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_local._.holder.v1~x.vendor._.bad.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "does not match pattern")
        ),
        _validate_type_schema(
            "gts.x.testref_local._.holder.v1~",
            True,
            "validate local reference holder schema",
        ),
    ]


class TestCaseXGtsRef_LocalRefMissingTarget(HttpRunner):
    config = Config("x-gts-instance-ref: local ref missing target").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register local ref schema with missing target")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_local_missing._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {"$$ref": "#/definitions/TargetRef"},
                },
                "definitions": {
                    "TargetRef": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_local_missing._.target.v1~",
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_local_missing._.holder.v1~",
            False,
            "reject local reference holder schema with missing target",
        ),
    ]


class TestCaseXGtsRef_AnnotationDataIgnored(HttpRunner):
    config = Config("entity reference: annotation data is not a subschema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with reference-keyword-shaped annotation data")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_annotation._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "payload": {
                        "type": "object",
                        "default": {
                            "x-gts-type-ref": "not-a-gts-id",
                            "x-gts-ref": "not-a-gts-id",
                        },
                        "const": {
                            "x-gts-instance-ref": (
                                "gts.x.testref_annotation._.missing.v1~"
                            ),
                        },
                        "examples": [
                            {"x-gts-type-ref": 42, "x-gts-instance-ref": 42},
                        ],
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_annotation._.holder.v1~",
            True,
            "accept reference-keyword-shaped values in annotation data",
        ),
    ]


class TestCaseXGtsRef_PropertyNamedKeyword(HttpRunner):
    config = Config("entity reference: property named like the keyword").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with properties named like reference keywords")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_property_name._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "x-gts-ref": {"type": "string"},
                    "x-gts-type-ref": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_property_name._.missing.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_property_name._.holder.v1~",
            False,
            "reject missing target under a property named x-gts-type-ref",
        ),
    ]


class TestCaseXGtsRef_RootLocalReference(HttpRunner):
    """A bare ``$ref: "#"`` must traverse the complete root schema.

    Existing local-reference coverage uses ``#/...`` pointers into a
    subschema. This case is distinct: a recursive child points to the root
    document itself, and the nested ``x-gts-instance-ref`` must still be validated.
    """
    config = Config("x-gts-instance-ref: root local reference").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register root local reference target schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_root._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register root local reference schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_root._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "link": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_root._.target.v1~",
                    },
                    "child": {"$$ref": "#"},
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register root local reference invalid instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_root._.holder.v1~x.vendor._.bad.v1",
                "child": {"link": "gts.x.other._.target.v1~x.vendor._.bad.v1"},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate root local reference invalid instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_root._.holder.v1~x.vendor._.bad.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "does not match pattern")
        ),
    ]


class TestCaseXGtsRef_WildcardPattern(HttpRunner):
    """x-gts-instance-ref: arbitrary wildcard patterns (not just ``gts.*``).

    §9.6.1: the constraint value may be any well-formed GTS wildcard pattern
    (§10), e.g. ``gts.x.testref_wild.am.*``. The field value must be a
    syntactically valid GTS id that matches the pattern. Registry presence and
    target validity then follow the selected gts-ref-validation mode.
    """
    config = Config("x-gts-instance-ref: arbitrary wildcard pattern").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Two target types under the gts.x.testref_wild.am.* family.
        Step(
            RunRequest("register am.user target schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wild.am.user.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register am.role target schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wild.am.role.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"kind": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # A concrete instance of am.user (the value a good ref resolves to).
        Step(
            RunRequest("register am.user instance")
            .post("/entities")
            .with_json({
                "kind": "user",
                "id": "gts.x.testref_wild.am.user.v1~x.vendor._.bob.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Holder schema: ref constrained by the wildcard family pattern.
        Step(
            RunRequest("register holder schema with wildcard x-gts-instance-ref")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wild._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_wild.am.*",
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Positive: ref matches the pattern AND is a registered entity.
        Step(
            RunRequest("register valid holder instance - registered match")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wild._.holder.v1~x.vendor._.ok.v1",
                "ref": "gts.x.testref_wild.am.user.v1~x.vendor._.bob.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate holder - wildcard value resolves, should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_wild._.holder.v1~x.vendor._.ok.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Negative 1: matches the pattern but the value is never registered.
        Step(
            RunRequest("register holder instance - matches pattern, unregistered value")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wild._.holder.v1~x.vendor._.ghost.v1",
                "ref": "gts.x.testref_wild.am.user.v1~x.vendor._.nobody.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_wild._.holder.v1~x.vendor._.ghost.v1",
            True,
            "none mode accepts matching unregistered wildcard value",
            gts_ref_validation="none",
        ),
        _validate_instance(
            "gts.x.testref_wild._.holder.v1~x.vendor._.ghost.v1",
            False,
            "any-present mode rejects matching unregistered wildcard value",
            gts_ref_validation="any-present",
        ),
        _validate_instance(
            "gts.x.testref_wild._.holder.v1~x.vendor._.ghost.v1",
            False,
            "any-valid mode rejects matching unregistered wildcard value",
            gts_ref_validation="any-valid",
        ),
        # Negative 2: valid GTS id but does not match the wildcard family.
        Step(
            RunRequest("register holder instance - value outside the pattern")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wild._.holder.v1~x.vendor._.wrong.v1",
                "ref": "gts.x.testref_wild.other.thing.v1~x.vendor._.x.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_wild._.holder.v1~x.vendor._.wrong.v1",
            False,
            "none mode still rejects value outside wildcard family",
            gts_ref_validation="none",
        ),
        # Negative 3: value is not a syntactically valid GTS identifier.
        Step(
            RunRequest("register holder instance - non-GTS value")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wild._.holder.v1~x.vendor._.badid.v1",
                "ref": "not a gts id",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate holder - non-GTS value should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_wild._.holder.v1~x.vendor._.badid.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_TildeWildcardPattern(HttpRunner):
    """x-gts-type-ref: ``...v1~*`` wildcard covers the base type and its descendants.

    Per §3.5/§10, ``gts....stream.v1~*`` matches the type ``...stream.v1~``
    itself as well as any entity derived from it. Registry lookup and target
    validity follow the selected gts-ref-validation mode.
    """
    config = Config("x-gts-type-ref: tilde wildcard pattern").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Base stream type + one registered derived stream type.
        Step(
            RunRequest("register stream base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wild.events.stream.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"name": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived stream schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wild.events.stream.v1~x.vendor._.orders.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.testref_wild.events.stream.v1~"}],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Holder schema constrained by the ~* wildcard.
        Step(
            RunRequest("register holder schema with tilde wildcard x-gts-type-ref")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wild.events.streamholder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "streamRef"],
                "properties": {
                    "id": {"type": "string"},
                    "streamRef": {
                        "type": "string",
                        "x-gts-type-ref": "gts.x.testref_wild.events.stream.v1~*",
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Positive: ref is the base type itself (matches ~* and is registered).
        Step(
            RunRequest("register holder instance - base type ref")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wild.events.streamholder.v1~x.vendor._.a.v1",
                "streamRef": "gts.x.testref_wild.events.stream.v1~",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate holder - base type ref should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_wild.events.streamholder.v1~x.vendor._.a.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Positive: ref is a registered derived type (matches ~*).
        Step(
            RunRequest("register holder instance - derived type ref")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wild.events.streamholder.v1~x.vendor._.b.v1",
                "streamRef": "gts.x.testref_wild.events.stream.v1~x.vendor._.orders.v1~",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate holder - registered derived ref should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_wild.events.streamholder.v1~x.vendor._.b.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Negative: matches ~* but the derived value is not registered.
        Step(
            RunRequest("register holder instance - unregistered derived ref")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wild.events.streamholder.v1~x.vendor._.c.v1",
                "streamRef": "gts.x.testref_wild.events.stream.v1~x.vendor._.ghost.v1~",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate holder - unregistered derived ref should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_wild.events.streamholder.v1~x.vendor._.c.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_ReferencedInstanceValidationModes(HttpRunner):
    config = Config("x-gts-instance-ref: referenced instance validation modes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register x-gts-instance-ref target type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_validity._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register invalid x-gts-instance-ref target instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_validity._.target.v1~x.vendor._.invalid.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate x-gts-instance-ref target instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": (
                    "gts.x.testref_validity._.target.v1~"
                    "x.vendor._.invalid.v1"
                ),
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("register x-gts-instance-ref holder type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_validity._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_validity._.target.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_validity._.holder.v1~",
            True,
            "validate holder type - referenced constraint type is present",
        ),
        Step(
            RunRequest("register holder referencing invalid instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_validity._.holder.v1~x.vendor._.invalid.v1",
                "ref": "gts.x.testref_validity._.target.v1~x.vendor._.invalid.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_validity._.holder.v1~x.vendor._.invalid.v1",
            True,
            "none mode ignores referenced instance presence and validity",
            gts_ref_validation="none",
        ),
        _validate_instance(
            "gts.x.testref_validity._.holder.v1~x.vendor._.invalid.v1",
            True,
            "any-present mode accepts present invalid referenced instance",
            gts_ref_validation="any-present",
        ),
        _validate_instance(
            "gts.x.testref_validity._.holder.v1~x.vendor._.invalid.v1",
            False,
            "any-valid mode rejects invalid referenced instance",
            gts_ref_validation="any-valid",
        ),
        _validate_instance(
            "gts.x.testref_validity._.holder.v1~x.vendor._.invalid.v1",
            False,
            "default mode remains any-valid",
        ),
    ]


class TestCaseXGtsRef_ConstraintValidationModes(HttpRunner):
    config = Config("x-gts-instance-ref: constraint validation modes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register invalid x-gts-instance-ref constraint type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_constraint._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                    "required": ["retention"],
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register holder using invalid x-gts-instance-ref constraint type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_constraint._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_constraint._.target.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_constraint._.target.v1~",
            False,
            "validate constraint type - required trait is unresolved",
        ),
        _validate_type_schema(
            "gts.x.testref_constraint._.holder.v1~",
            True,
            "none mode ignores constraint target presence and validity",
            gts_ref_validation="none",
        ),
        _validate_type_schema(
            "gts.x.testref_constraint._.holder.v1~",
            True,
            "any-present mode accepts present invalid constraint target",
            gts_ref_validation="any-present",
        ),
        _validate_type_schema(
            "gts.x.testref_constraint._.holder.v1~",
            False,
            "any-valid mode rejects invalid constraint target",
            gts_ref_validation="any-valid",
        ),
        _validate_type_schema(
            "gts.x.testref_constraint._.holder.v1~",
            False,
            "default mode remains any-valid",
        ),
    ]


class TestCaseXGtsRef_WildcardValidationModes(HttpRunner):
    config = Config("x-gts-instance-ref wildcard validation modes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register holder whose wildcard has no registry match")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wildpresence._.empty_holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_wildpresence.empty.*",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_wildpresence._.empty_holder.v1~",
            True,
            "none mode accepts wildcard constraint with no registry match",
            gts_ref_validation="none",
        ),
        _validate_type_schema(
            "gts.x.testref_wildpresence._.empty_holder.v1~",
            False,
            "any-present mode rejects wildcard constraint with no registered match",
            gts_ref_validation="any-present",
        ),
        _validate_type_schema(
            "gts.x.testref_wildpresence._.empty_holder.v1~",
            False,
            "any-valid mode rejects wildcard constraint with no registered match",
            gts_ref_validation="any-valid",
        ),
        Step(
            RunRequest("register invalid wildcard target type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wildvalidity.target.item.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
                "x-gts-traits-schema": {
                    "type": "object",
                    "required": ["retention"],
                    "properties": {"retention": {"type": "string"}},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_wildvalidity.target.item.v1~",
            False,
            "validate wildcard target type - required trait is unresolved",
        ),
        Step(
            RunRequest("register invalid wildcard target instance")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.testref_wildvalidity.target.item.v1~"
                    "x.vendor._.invalid.v1"
                ),
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register wildcard holder type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wildvalidity._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "x-gts-instance-ref": "gts.x.testref_wildvalidity.target.*",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_wildvalidity._.holder.v1~",
            True,
            "none mode ignores wildcard target validity",
            gts_ref_validation="none",
        ),
        _validate_type_schema(
            "gts.x.testref_wildvalidity._.holder.v1~",
            True,
            "any-present mode accepts a registered invalid wildcard match",
            gts_ref_validation="any-present",
        ),
        _validate_type_schema(
            "gts.x.testref_wildvalidity._.holder.v1~",
            False,
            "any-valid mode rejects wildcard with only invalid registered matches",
            gts_ref_validation="any-valid",
        ),
        # The only valid registered match is a Type ID. It witnesses the
        # instance-reference wildcard operand: operand lookup ignores kind.
        Step(
            RunRequest("register valid wildcard target type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_wildvalidity.target.valid.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_wildvalidity._.holder.v1~",
            True,
            "any-valid mode accepts wildcard with at least one valid registered match",
            gts_ref_validation="any-valid",
        ),
        Step(
            RunRequest("register wildcard holder referencing invalid instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_wildvalidity._.holder.v1~x.vendor._.invalid.v1",
                "ref": (
                    "gts.x.testref_wildvalidity.target.item.v1~"
                    "x.vendor._.invalid.v1"
                ),
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            (
                "gts.x.testref_wildvalidity.target.item.v1~"
                "x.vendor._.invalid.v1"
            ),
            False,
            "validate wildcard target instance - name is missing",
        ),
        _validate_instance(
            "gts.x.testref_wildvalidity._.holder.v1~x.vendor._.invalid.v1",
            True,
            "none mode ignores referenced wildcard target validity",
            gts_ref_validation="none",
        ),
        _validate_instance(
            "gts.x.testref_wildvalidity._.holder.v1~x.vendor._.invalid.v1",
            True,
            "any-present mode accepts present invalid wildcard target",
            gts_ref_validation="any-present",
        ),
        _validate_instance(
            "gts.x.testref_wildvalidity._.holder.v1~x.vendor._.invalid.v1",
            False,
            "any-valid mode rejects invalid wildcard target value",
            gts_ref_validation="any-valid",
        ),
    ]


class TestCaseXGtsRef_RegistrationValidationModes(HttpRunner):
    config = Config("x-gts-type-ref registration validation modes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register invalid constraint target")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_regmode._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "required": ["retention"],
                    "properties": {"retention": {"type": "string"}},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("none mode registers holder with missing constraint target")
            .post("/entities?validate=true&gts-ref-validation=none")
            .with_json({
                "$$id": "gts://gts.x.testref_regmode._.none.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "x-gts-type-ref": "gts.x.testref_regmode._.missing.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("any-present mode rejects missing constraint target")
            .post("/entities?validate=true&gts-ref-validation=any-present")
            .with_json({
                "$$id": "gts://gts.x.testref_regmode._.presence_missing.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "x-gts-type-ref": "gts.x.testref_regmode._.missing.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("any-present mode registers holder with invalid constraint target")
            .post("/entities?validate=true&gts-ref-validation=any-present")
            .with_json({
                "$$id": "gts://gts.x.testref_regmode._.presence.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "x-gts-type-ref": "gts.x.testref_regmode._.target.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("any-valid mode rejects invalid constraint target")
            .post("/entities?validate=true&gts-ref-validation=any-valid")
            .with_json({
                "$$id": "gts://gts.x.testref_regmode._.full.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "x-gts-type-ref": "gts.x.testref_regmode._.target.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("reject unknown gts-ref-validation mode")
            .post("/validate-type-schema?gts-ref-validation=unknown")
            .with_json({"type_id": "gts.x.testref_regmode._.target.v1~"})
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseXGtsRef_TupleAdditionalItems(HttpRunner):
    config = Config("x-gts-instance-ref: Draft-07 tuple additionalItems").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register tuple overflow target type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_tuple._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"id": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register tuple overflow target instance")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.testref_tuple._.target.v1~"
                    "x.vendor._.registered.v1"
                ),
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register tuple additionalItems holder type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_tuple._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "refs"],
                "properties": {
                    "id": {"type": "string"},
                    "refs": {
                        "type": "array",
                        "items": [{"type": "string"}],
                        "additionalItems": {
                            "type": "string",
                            "x-gts-instance-ref": "gts.x.testref_tuple._.target.v1~",
                        },
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register holder with valid tuple overflow reference")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_tuple._.holder.v1~x.vendor._.valid.v1",
                "refs": [
                    "tuple-prefix",
                    (
                        "gts.x.testref_tuple._.target.v1~"
                        "x.vendor._.registered.v1"
                    ),
                ],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_tuple._.holder.v1~x.vendor._.valid.v1",
            True,
            "validate registered tuple overflow reference",
        ),
        Step(
            RunRequest("register holder with missing tuple overflow reference")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_tuple._.holder.v1~x.vendor._.invalid.v1",
                "refs": [
                    "tuple-prefix",
                    (
                        "gts.x.testref_tuple._.target.v1~"
                        "x.vendor._.missing.v1"
                    ),
                ],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_tuple._.holder.v1~x.vendor._.invalid.v1",
            False,
            "reject missing tuple overflow reference",
        ),
        Step(
            RunRequest("register tuple holder with missing constraint type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_tuple._.missing_holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "array",
                "items": [{"type": "string"}],
                "additionalItems": {
                    "type": "string",
                    "x-gts-instance-ref": "gts.x.testref_tuple._.missing_target.v1~",
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_tuple._.missing_holder.v1~",
            False,
            "reject additionalItems schema with missing constraint type",
        ),
    ]


class TestCaseXGtsRef_PrefixItems(HttpRunner):
    config = Config("x-gts-instance-ref: Draft 2020-12 prefixItems").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register prefixItems overflow target type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_prefixitems._.target.v1~",
                "$$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"id": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register prefixItems overflow target instance")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.testref_prefixitems._.target.v1~"
                    "x.vendor._.registered.v1"
                ),
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register prefixItems holder type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_prefixitems._.holder.v1~",
                "$$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["id", "refs"],
                "properties": {
                    "id": {"type": "string"},
                    "refs": {
                        "type": "array",
                        "prefixItems": [{"type": "string"}],
                        "items": {
                            "type": "string",
                            "x-gts-instance-ref": "gts.x.testref_prefixitems._.target.v1~",
                        },
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_prefixitems._.holder.v1~",
            True,
            "validate prefixItems holder type",
        ),
        Step(
            RunRequest("register holder with valid prefixItems overflow reference")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.testref_prefixitems._.holder.v1~"
                    "x.vendor._.valid.v1"
                ),
                "refs": [
                    "tuple-prefix",
                    (
                        "gts.x.testref_prefixitems._.target.v1~"
                        "x.vendor._.registered.v1"
                    ),
                ],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            (
                "gts.x.testref_prefixitems._.holder.v1~"
                "x.vendor._.valid.v1"
            ),
            True,
            "validate registered prefixItems overflow reference",
        ),
        Step(
            RunRequest("register holder with missing prefixItems overflow reference")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.testref_prefixitems._.holder.v1~"
                    "x.vendor._.invalid.v1"
                ),
                "refs": [
                    "tuple-prefix",
                    (
                        "gts.x.testref_prefixitems._.target.v1~"
                        "x.vendor._.missing.v1"
                    ),
                ],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            (
                "gts.x.testref_prefixitems._.holder.v1~"
                "x.vendor._.invalid.v1"
            ),
            False,
            "reject missing prefixItems overflow reference",
        ),
    ]


class TestCaseXGtsRef_NullableReference(HttpRunner):
    """x-gts-instance-ref: nullable reference via a combinator with a neutral branch.

    The common "optional reference" shape mixes an x-gts-instance-ref branch with a
    plain structural branch that carries no x-gts-instance-ref, e.g.::

        "oneOf": [
            {"type": "string", "x-gts-instance-ref": "gts.a._.b.v1~"},
            {"type": "null"}
        ]

    The neutral ``{"type": "null"}`` branch has no x-gts-instance-ref, so the standard
    JSON Schema engine already enforces which branch a value belongs to. An
    implementation that runs its own x-gts-instance-ref combinator pass must treat a
    branch without an x-gts-instance-ref as neutral rather than a branch that always
    "matches"; otherwise a valid string reference counts as matching *both*
    branches and a valid value is rejected. Earlier combinator coverage only
    exercised combinators where *every* branch carried an x-gts-instance-ref, so this
    mixed shape was never checked.
    """

    config = Config("x-gts-instance-ref: nullable reference").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Target schema + a registered instance to reference.
        Step(
            RunRequest("register nullable target schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_nullable._.target.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register nullable target instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_nullable._.target.v1~x.vendor._.t1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # oneOf: nullable reference (string+x-gts-instance-ref OR null).
        Step(
            RunRequest("register nullable oneOf holder schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_nullable._.oneof_holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "oneOf": [
                            {
                                "type": "string",
                                "x-gts-instance-ref": "gts.x.testref_nullable._.target.v1~",
                            },
                            {"type": "null"},
                        ]
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # A valid string reference must match exactly the x-gts-instance-ref branch.
        Step(
            RunRequest("register nullable oneOf instance - valid reference")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_nullable._.target.v1~x.vendor._.t1.v1.0",
                "id": "gts.x.testref_nullable._.oneof_holder.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_nullable._.oneof_holder.v1~x.vendor._.i1.v1.0",
            True,
            "nullable oneOf must accept a valid reference",
        ),
        # A null value matches the neutral branch only.
        Step(
            RunRequest("register nullable oneOf instance - null value")
            .post("/entities")
            .with_json({
                "ref": None,
                "id": "gts.x.testref_nullable._.oneof_holder.v1~x.vendor._.i2.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_nullable._.oneof_holder.v1~x.vendor._.i2.v1.0",
            True,
            "nullable oneOf must accept null",
        ),
        # anyOf: nullable reference (string+x-gts-instance-ref OR null).
        Step(
            RunRequest("register nullable anyOf holder schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_nullable._.anyof_holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "anyOf": [
                            {
                                "type": "string",
                                "x-gts-instance-ref": "gts.x.testref_nullable._.target.v1~",
                            },
                            {"type": "null"},
                        ]
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register nullable anyOf instance - valid reference")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_nullable._.target.v1~x.vendor._.t1.v1.0",
                "id": "gts.x.testref_nullable._.anyof_holder.v1~x.vendor._.i1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_nullable._.anyof_holder.v1~x.vendor._.i1.v1.0",
            True,
            "nullable anyOf must accept a valid reference",
        ),
        Step(
            RunRequest("register nullable anyOf instance - null value")
            .post("/entities")
            .with_json({
                "ref": None,
                "id": "gts.x.testref_nullable._.anyof_holder.v1~x.vendor._.i2.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_nullable._.anyof_holder.v1~x.vendor._.i2.v1.0",
            True,
            "nullable anyOf must accept null",
        ),
    ]


class TestCaseXGtsRef_SelfRefInOneOf(HttpRunner):
    """x-gts-instance-ref: a /$id branch inside oneOf must not shadow a sibling branch.

    ``oneOf`` requires exactly one branch to match. When one branch is
    ``{"x-gts-instance-ref": "/$id"}`` and another is a concrete GTS pattern, an
    implementation must resolve ``/$id`` to the selected type while selecting
    the matching branch. If ``/$id`` is instead treated as always-matching
    (e.g. a JSON Schema engine that evaluates x-gts-instance-ref as a keyword but
    short-circuits ``/$id`` to "valid" because it lacks the selected type),
    a value that matches only the sibling pattern satisfies *both* branches
    and the exactly-one rule wrongly rejects a valid value.

    Prior oneOf coverage only used concrete patterns in every branch, so this
    /$id-versus-concrete combination was never exercised.
    """

    config = Config("x-gts-instance-ref: /$$id inside oneOf").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # A sibling target type + a registered instance to reference.
        Step(
            RunRequest("register selfcomb other schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_selfcomb._.other.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register selfcomb other instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_selfcomb._.other.v1~x.vendor._.o1.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Holder type: ref must match exactly one of /$id (this type) or other.
        Step(
            RunRequest("register selfcomb holder schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_selfcomb._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "oneOf": [
                            {"x-gts-instance-ref": "/$$id"},
                            {"x-gts-instance-ref": "gts.x.testref_selfcomb._.other.v1~"},
                        ],
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # ref matches ONLY the concrete sibling branch. /$id (this holder type)
        # does not match an "other"-typed id, so exactly one branch matches.
        Step(
            RunRequest("register holder instance referencing the sibling")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_selfcomb._.other.v1~x.vendor._.o1.v1.0",
                "id": "gts.x.testref_selfcomb._.holder.v1~x.vendor._.href_other.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_selfcomb._.holder.v1~x.vendor._.href_other.v1.0",
            True,
            "oneOf with a /$$id branch must accept a value matching only the sibling",
        ),
        # ref matches ONLY the /$id branch: the referenced id is itself a holder
        # instance (so it matches this selected type) and is not an "other" id.
        Step(
            RunRequest("register holder instance referencing another holder instance")
            .post("/entities")
            .with_json({
                "ref": "gts.x.testref_selfcomb._.holder.v1~x.vendor._.href_other.v1.0",
                "id": "gts.x.testref_selfcomb._.holder.v1~x.vendor._.href_self.v1.0",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.testref_selfcomb._.holder.v1~x.vendor._.href_self.v1.0",
            True,
            "oneOf with a /$$id branch must accept a value matching only /$$id",
        ),
    ]


@pytest.mark.parametrize("keyword", ["x-gts-type-ref", "x-gts-instance-ref"])
@pytest.mark.parametrize("operand", ["universal", "wildcard", "concrete"])
@pytest.mark.parametrize("mode", ["none", "any-present", "any-valid"])
def test_entity_ref_payload_requires_concrete_ids_of_required_kind(
    gts_api, schema_dialect, mode, operand, keyword
):
    """No operand permits wildcard strings or the other kind in the payload.

    Under ``gts.*`` every wildcard value below would be covered if pattern
    coverage leaked into entity references; ``target~*`` and ``target~`` would
    cover the type-scoped ones. Both concrete candidates are registered and
    valid, so the wrong-kind rejection cannot come from registry lookup.
    """
    api = gts_api
    target = api.register("target", {"type": "object"}, schema_dialect)
    target_instance = api.register_instance(target, {}, validate=True)
    operand_value = {
        "universal": "gts.*",
        "wildcard": target + "*",
        "concrete": target,
    }[operand]
    holder = api.register(
        "holder",
        {
            "type": "object",
            "required": ["value"],
            "properties": {"value": {"type": "string", keyword: operand_value}},
        },
        schema_dialect,
        mode=mode,
    )
    type_ref = keyword == "x-gts-type-ref"
    for name, concrete_id, valid in (
        ("concrete_type", target, type_ref),
        ("concrete_instance", target_instance, not type_ref),
    ):
        if valid:
            instance_id = api.register_instance(
                holder, {"value": concrete_id}, name=name, validate=True, mode=mode
            )
        else:
            api.register_instance(
                holder,
                {"value": concrete_id},
                name=name,
                validate=True,
                mode=mode,
                status=422,
            )
            instance_id = api.register_instance(
                holder, {"value": concrete_id}, name=name
            )
        api.check_instance(instance_id, valid=valid, mode=mode)
    for name, wildcard in (
        ("type_suffix_wildcard", target + "*"),
        ("type_family_wildcard", target.rsplit(".v", 1)[0] + ".*"),
        ("universal_wildcard", "gts.*"),
    ):
        # Registration with validation rejects the value in every mode.
        api.register_instance(
            holder,
            {"value": wildcard},
            name=name,
            validate=True,
            mode=mode,
            status=422,
        )
        instance_id = api.register_instance(holder, {"value": wildcard}, name=name)
        api.check_instance(instance_id, valid=False, mode=mode)


@pytest.mark.parametrize(
    "mode,valid",
    [("none", True), ("any-present", False), ("any-valid", False)],
)
def test_minor_flexible_reference_looks_up_the_actual_value(
    gts_api, schema_dialect, mode, valid
):
    """Matching an omitted minor does not replace exact registry lookup."""
    api = gts_api
    target_type = api.register("target", {"type": "object"}, schema_dialect)
    operand = target_type + "acme.prod._.uploads.v1"
    api.request(
        "POST",
        "/entities",
        params={"validate": "true", "gts-ref-validation": mode},
        json={"id": operand, "type": target_type},
    )
    holder = api.register(
        "holder",
        {
            "type": "object",
            "properties": {"ref": {"type": "string", "x-gts-instance-ref": operand}},
            "required": ["ref"],
        },
        schema_dialect,
        mode=mode,
    )
    instance = api.register_instance(holder, {"ref": operand + ".0"})
    api.check_instance(instance, valid=valid, mode=mode)


if __name__ == "__main__":
    TestCaseXGtsRef_PrefixAndSelfRef().test_start()
    TestCaseXGtsRef_OneOf().test_start()
    TestCaseXGtsRef_AnyOf().test_start()
    TestCaseXGtsRef_AllOf().test_start()
    TestCaseXGtsRef_NestedCombinators().test_start()
    TestCaseXGtsRef_WildcardPattern().test_start()
    TestCaseXGtsRef_TildeWildcardPattern().test_start()
    TestCaseXGtsRef_NullableReference().test_start()
    TestCaseXGtsRef_SelfRefInOneOf().test_start()
