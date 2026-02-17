"""Tests for x-gts-ref validation: prefix enforcement, JSON Pointer resolution, and combinator semantics."""

from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseXGtsRef_PrefixAndSelfRef(HttpRunner):
    """x-gts-ref: prefix enforcement and self-reference (./$id)"""
    config = Config("x-gts-ref: prefix and self-ref").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-ref prefix and self-reference test steps."""
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
                    "id": {"type": "string", "x-gts-ref": "/$$id"},
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
        # Register a module schema that references capability IDs by prefix and enforces ./$/id on its own type field
        Step(
            RunRequest("register module schema with x-gts-ref prefix and self-ref")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref._.module.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["type", "id", "capabilities"],
                "properties": {
                    "type": {"type": "string", "x-gts-ref": "/$$id"},
                    "id": {"type": "string"},
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string", "x-gts-ref": "gts.x.testref._.capability.v1~"},
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


class TestCaseXGtsRef_JsonPointer(HttpRunner):
    """x-gts-ref: JSON Pointer-style resolution: ./description, ./title, and nested ./properties/anchor/const"""
    config = Config("x-gts-ref: json-pointer resolution").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-ref JSON Pointer resolution test steps."""
        super().test_start()

    teststeps = [
        # Register schema with description/title, and nested anchor.const
        Step(
            RunRequest("register pointer schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref._.pointer.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "title": "PTR-TITLE",
                "description": "PTR-DESC",
                "type": "object",
                "properties": {
                    "id": {"type": "string", "x-gts-ref": "/$$id"},
                    "type": {"type": "string", "x-gts-ref": "/properties/id"},
                },
                "required": ["id"],
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register a valid instance that satisfies all x-gts-ref pointers
        Step(
            RunRequest("register valid pointer instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.testref._.pointer.v1~",
                "id": "gts.x.testref._.pointer.v1~x.vendor._.ptr_ok.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register valid pointer instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref._.capability.v1~",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate valid pointer instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref._.pointer.v1~x.vendor._.ptr_ok.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("get valid pointer instance")
            .get("/entities/gts.x.testref._.pointer.v1~x.vendor._.ptr_ok.v1")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.content.type", "gts.x.testref._.pointer.v1~")
            .assert_equal("body.content.id", "gts.x.testref._.pointer.v1~x.vendor._.ptr_ok.v1")
        ),
        # Register invalid instance (wrong refDesc)
        Step(
            RunRequest("register invalid pointer instance - wrong refDesc")
            .post("/entities")
            .with_json({
                "type": "gts.x.testref._.pointer.v1~",
                "id": "gts.x.testref._.wrong_pointer.v1~x.vendor._.ptr_bad_desc.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate invalid pointer instance - wrong refDesc should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref._.wrong_pointer.v1~x.vendor._.ptr_bad_desc.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_WrongGtsFormat(HttpRunner):
    """x-gts-ref: malformed GTS ID"""
    config = Config("x-gts-ref: malformed GTS ID").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-ref malformed GTS ID test steps."""
        super().test_start()

    teststeps = [
        # Register schema with malformed x-gts-ref, test 1
        Step(
            RunRequest("register pointer schema")
            .post("/entities?validation=true")
            .with_json({
                "$$id": "gts://gts.x.testref_malformed._.pointer.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "title": "PTR-TITLE",
                "description": "PTR-DESC",
                "type": "object",
                "properties": {
                    "id": {"type": "string", "x-gts-ref": "gts.x.y.z"},
                },
                "required": ["id"],
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "Invalid GTS identifier: gts.x.y.z")
        ),
        # Register schema with malformed x-gts-ref, test 2
        Step(
            RunRequest("register pointer schema")
            .post("/entities?validation=true")
            .with_json({
                "$$id": "gts://gts.x.testref_malformed._.pointer.v2~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "title": "PTR-TITLE",
                "description": "PTR-DESC",
                "type": "object",
                "properties": {
                    "id": {"type": "string", "x-gts-ref": "a.b.c"},
                },
                "required": ["id"],
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "x-gts-ref validation failed")
            .assert_contains("body.error", "a.b.c")
        ),
        # Register schema pointer to non-GTS const
        Step(
            RunRequest("register pointer schema")
            .post("/entities?validation=true")
            .with_json({
                "$$id": "gts://gts.x.testref_malformed._.pointer.v3~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "title": "PTR-TITLE",
                "description": "PTR-DESC",
                "type": "object",
                "properties": {
                    "some": {"type": "string", "const": "a.b.c"},
                    "id": {"type": "string", "x-gts-ref": "/properties/some/const"},
                },
                "required": ["id"],
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "x-gts-ref validation failed")
            .assert_contains("body.error", "a.b.c")
        ),
        # Register schema pointer to non-GTS const, without validation
        Step(
            RunRequest("register pointer schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_malformed._.pointer.v4~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "title": "PTR-TITLE",
                "description": "PTR-DESC",
                "type": "object",
                "properties": {
                    "some": {"type": "string", "const": "a.b.c"},
                    "id": {"type": "string", "x-gts-ref": "/properties/some/const"},
                },
                "required": ["id"],
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "alidation failed")
            .assert_contains("body.error", "a.b.c")
        ),
        # Validate previous pointer to non-GTS const
        Step(
            RunRequest("validate pointer schema")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.testref_malformed._.pointer.v4~x.vendor._.ptr_ok.v1"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        # Register schema correct reference
        Step(
            RunRequest("register pointer schema")
            .post("/entities?validation=true")
            .with_json({
                "$$id": "gts://gts.x.testref_malformed._.pointer.v5~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "title": "PTR-TITLE",
                "description": "PTR-DESC",
                "type": "object",
                "properties": {
                    "some": {"type": "string", "const": "gts.x.testref_malformed._.pointer.v5~"},
                    "id": {"type": "string", "x-gts-ref": "/properties/some/const"},
                },
                "required": ["id"],
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]

class TestCaseXGtsRef_OneOf(HttpRunner):
    """x-gts-ref: oneOf combinator - exactly one branch must match"""
    config = Config("x-gts-ref: oneOf combinator").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-ref oneOf combinator test steps."""
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
                            {"x-gts-ref": "gts.x.testref_comb._.target_a.v1~"},
                            {"x-gts-ref": "gts.x.testref_comb._.target_b.v1~"},
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
                            {"x-gts-ref": "gts.x.testref_comb.*"},
                            {"x-gts-ref": "gts.x.testref_comb._.target_a.v1~"},
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


class TestCaseXGtsRef_AnyOf(HttpRunner):
    """x-gts-ref: anyOf combinator - at least one branch must match"""
    config = Config("x-gts-ref: anyOf combinator").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-ref anyOf combinator test steps."""
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
                            {"x-gts-ref": "gts.x.testref_comb._.target_a.v1~"},
                            {"x-gts-ref": "gts.x.testref_comb._.target_b.v1~"},
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
    """x-gts-ref: allOf combinator - all branches must match"""
    config = Config("x-gts-ref: allOf combinator").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-ref allOf combinator test steps."""
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
                            {"x-gts-ref": "gts.x.testref_comb._.target_a.v1~"},
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
                            {"x-gts-ref": "gts.x.testref_comb._.target_a.v1~"},
                            {"x-gts-ref": "gts.x.testref_comb._.target_b.v1~"},
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
    """x-gts-ref: nested combinators - allOf wrapping oneOf"""
    config = Config("x-gts-ref: nested combinators").base_url(get_gts_base_url())

    def test_start(self):
        """Run x-gts-ref nested combinator test steps."""
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
                                    {"x-gts-ref": "gts.x.testref_comb._.target_a.v1~"},
                                    {"x-gts-ref": "gts.x.testref_comb._.target_b.v1~"},
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


if __name__ == "__main__":
    TestCaseXGtsRef_PrefixAndSelfRef().test_start()
    TestCaseXGtsRef_JsonPointer().test_start()
    TestCaseXGtsRef_WrongGtsFormat().test_start()
    TestCaseXGtsRef_OneOf().test_start()
    TestCaseXGtsRef_AnyOf().test_start()
    TestCaseXGtsRef_AllOf().test_start()
    TestCaseXGtsRef_NestedCombinators().test_start()
