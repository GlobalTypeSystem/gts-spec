"""Tests for x-gts-ref matching, /$id semantics, and combinator traversal."""

from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    validate_instance as _validate_instance,
    validate_type_schema as _validate_type_schema,
)
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseXGtsRef_PrefixAndSelfRef(HttpRunner):
    """x-gts-ref: prefix enforcement and /$id self-reference."""
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
        # Register a module schema that references capability IDs by prefix and enforces /$id on its own type field
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


class TestCaseXGtsRef_ExactRefSegmentBoundary(HttpRunner):
    """x-gts-ref: an exact (non-wildcard, non-`~`) reference matches on a segment
    boundary, not by raw string prefix.

    An exact instance constraint ``...thing.v1`` must accept only that identifier,
    not a textual superset such as ``...thing.v12``. A naive ``value.startsWith(pattern)``
    check leaks across the version boundary and wrongly accepts a reference to a
    *different* registered instance, so validation would pass an unrelated entity.
    """

    config = Config("x-gts-ref: exact ref segment boundary").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Base type whose instances are referenced by an exact x-gts-ref.
        Step(
            RunRequest("register exact-ref target type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.refbound._.item.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Two instances where one id is a textual prefix of the other (v1 vs v12).
        Step(
            RunRequest("register exact target instance v1")
            .post("/entities")
            .with_json({"id": "gts.x.refbound._.item.v1~x.vendor._.thing.v1"})
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register sibling target instance v12")
            .post("/entities")
            .with_json({"id": "gts.x.refbound._.item.v1~x.vendor._.thing.v12"})
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Holder schema constrains `ref` to the EXACT v1 instance.
        Step(
            RunRequest("register holder schema with exact instance ref")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.refbound._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "x-gts-ref": "gts.x.refbound._.item.v1~x.vendor._.thing.v1",
                    },
                },
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Exact match -> valid.
        Step(
            RunRequest("register holder instance referencing exact v1")
            .post("/entities")
            .with_json({
                "ref": "gts.x.refbound._.item.v1~x.vendor._.thing.v1",
                "id": "gts.x.refbound._.holder.v1~x.vendor._.h1.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.refbound._.holder.v1~x.vendor._.h1.v1",
            True,
            "exact instance reference must pass",
        ),
        # Prefix superset (v12) -> must be rejected on the segment boundary.
        Step(
            RunRequest("register holder instance referencing superset v12")
            .post("/entities")
            .with_json({
                "ref": "gts.x.refbound._.item.v1~x.vendor._.thing.v12",
                "id": "gts.x.refbound._.holder.v1~x.vendor._.h2.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            "gts.x.refbound._.holder.v1~x.vendor._.h2.v1",
            False,
            "prefix-superset reference must fail (segment boundary)",
        ),
    ]


class TestCaseXGtsRef_UnsupportedPointers(HttpRunner):
    """Every slash-prefixed x-gts-ref operand except /$id is prohibited."""

    config = Config("x-gts-ref: reject unsupported pointers").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject pointer to a concrete GTS const")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_pointer._.const.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "anchor": {
                        "type": "string",
                        "const": "gts.x.testref_pointer._.target.v1~",
                    },
                    "ref": {
                        "type": "string",
                        "x-gts-ref": "/properties/anchor/const",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("reject pointer chaining even when reference checks are disabled")
            .post("/entities?validate=true&gts-ref-validation=none")
            .with_json({
                "$$id": "gts://gts.x.testref_pointer._.chain.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "anchor": {"type": "string", "x-gts-ref": "/$$id"},
                    "ref": {
                        "type": "string",
                        "x-gts-ref": "/properties/anchor",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseXGtsRef_SelectedLeafSelfRef(HttpRunner):
    """/$id remains rooted at the selected leaf through schema composition."""

    config = Config("x-gts-ref: /$$id uses derived type schema id").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    base_id = "gts.x.testref_selfref._.document.v1~"
    derived_id = base_id + "x.testref_selfref._.invoice.v1~"
    sibling_id = base_id + "x.testref_selfref._.credit_note.v1~"
    further_id = derived_id + "x.testref_selfref._.priority_invoice.v1~"
    no_ref_id = base_id + "x.testref_selfref._.standalone.v1~"
    referenced_instance_id = derived_id + "x.testref_selfref._.invoice_001.v1"
    further_instance_id = further_id + "x.testref_selfref._.priority_001.v1"

    teststeps = [
        Step(
            RunRequest("register base with /$id constraint")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{base_id}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "entityRef"],
                "properties": {
                    "id": {"type": "string"},
                    "entityRef": {"type": "string", "x-gts-ref": "/$$id"},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived selected leaf")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{derived_id}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": f"gts://{base_id}"}],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register sibling type")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{sibling_id}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": f"gts://{base_id}"}],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register referenced instance of selected leaf")
            .post("/entities")
            .with_json({
                "id": referenced_instance_id,
                "entityRef": derived_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register selected leaf instance referring to leaf type")
            .post("/entities")
            .with_json({
                "id": derived_id + "x.testref_selfref._.type_ref.v1",
                "entityRef": derived_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            derived_id + "x.testref_selfref._.type_ref.v1",
            True,
            "accept selected leaf type under inherited /$id",
        ),
        Step(
            RunRequest("register selected leaf instance referring to leaf instance")
            .post("/entities")
            .with_json({
                "id": derived_id + "x.testref_selfref._.instance_ref.v1",
                "entityRef": referenced_instance_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            derived_id + "x.testref_selfref._.instance_ref.v1",
            True,
            "accept instance rooted at selected leaf under inherited /$id",
        ),
        Step(
            RunRequest("register selected leaf instance referring to base")
            .post("/entities")
            .with_json({
                "id": derived_id + "x.testref_selfref._.base_ref.v1",
                "entityRef": base_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            derived_id + "x.testref_selfref._.base_ref.v1",
            False,
            "reject base type because /$id is rebound to selected leaf",
        ),
        Step(
            RunRequest("register selected leaf instance referring to sibling")
            .post("/entities")
            .with_json({
                "id": derived_id + "x.testref_selfref._.sibling_ref.v1",
                "entityRef": sibling_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            derived_id + "x.testref_selfref._.sibling_ref.v1",
            False,
            "reject sibling type under selected-leaf /$id",
        ),
        Step(
            RunRequest("register selected leaf instance with malformed reference")
            .post("/entities")
            .with_json({
                "id": derived_id + "x.testref_selfref._.malformed_ref.v1",
                "entityRef": "not-a-gts-id",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            derived_id + "x.testref_selfref._.malformed_ref.v1",
            False,
            "reject malformed identifier under inherited /$id",
        ),
        Step(
            RunRequest("register type further derived from selected leaf")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{further_id}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": f"gts://{derived_id}"}],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register instance of further-derived type")
            .post("/entities")
            .with_json({
                "id": further_instance_id,
                "entityRef": further_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            further_instance_id,
            True,
            "accept further-derived instance rooted at its selected leaf",
        ),
        Step(
            RunRequest("register invoice referring to further-derived type")
            .post("/entities")
            .with_json({
                "id": derived_id + "x.testref_selfref._.further_type_ref.v1",
                "entityRef": further_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            derived_id + "x.testref_selfref._.further_type_ref.v1",
            True,
            "accept further-derived type under invoice-rooted /$id",
        ),
        Step(
            RunRequest("register invoice referring to further-derived instance")
            .post("/entities")
            .with_json({
                "id": derived_id + "x.testref_selfref._.further_instance_ref.v1",
                "entityRef": further_instance_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            derived_id + "x.testref_selfref._.further_instance_ref.v1",
            True,
            "accept further-derived instance under invoice-rooted /$id",
        ),
        Step(
            RunRequest("register further-derived instance referring to ancestor")
            .post("/entities")
            .with_json({
                "id": further_id + "x.testref_selfref._.ancestor_ref.v1",
                "entityRef": derived_id,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            further_id + "x.testref_selfref._.ancestor_ref.v1",
            False,
            "reject ancestor when /$id is rebound to further-derived leaf",
        ),
        Step(
            RunRequest("register chained type without authored schema reference")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{no_ref_id}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "entityRef"],
                "properties": {
                    "id": {"type": "string"},
                    "entityRef": {"type": "string"},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register standalone chained instance with arbitrary string")
            .post("/entities")
            .with_json({
                "id": no_ref_id + "x.testref_selfref._.arbitrary.v1",
                "entityRef": "not-a-gts-id",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            no_ref_id + "x.testref_selfref._.arbitrary.v1",
            True,
            "do not import /$id through chained identifier alone",
        ),
        Step(
            RunRequest("register schema with inline composed /$id constraint")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_selfref._.inline.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{
                    "type": "object",
                    "required": ["id", "entityRef"],
                    "properties": {
                        "id": {"type": "string"},
                        "entityRef": {"type": "string", "x-gts-ref": "/$$id"},
                    },
                }],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register inline composed self reference instance")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.testref_selfref._.inline.v1~"
                    "x.testref_selfref._.self.v1"
                ),
                "entityRef": "gts.x.testref_selfref._.inline.v1~",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_instance(
            (
                "gts.x.testref_selfref._.inline.v1~"
                "x.testref_selfref._.self.v1"
            ),
            True,
            "accept inline allOf /$id rooted at outer selected schema",
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
        # Reject unsupported pointer even when its target is not a GTS ID
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
        ),
        # Pointer syntax is rejected during registration without validation
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
        ),
        Step(
            RunRequest("reject legacy dot-slash x-gts-ref pointer")
            .post("/entities?validation=true")
            .with_json({
                "$$id": "gts://gts.x.testref_malformed._.pointer.v6~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "id": {"type": "string", "x-gts-ref": "./$$id"},
                },
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
        # Reject unsupported pointer even when it resolves to a valid GTS ID
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
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
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


class TestCaseXGtsRef_OneOfSharedStructuralKeywords(HttpRunner):
    """x-gts-ref: oneOf branches that share structural keywords and differ only
    by x-gts-ref must still validate.

    The JSON Schema engine does not see x-gts-ref (its exclusivity is enforced
    separately). Branches like ``{"type":"string","x-gts-ref":"...a~"}`` and
    ``{"type":"string","x-gts-ref":"...b~"}`` are structurally identical once
    x-gts-ref is set aside, so an implementation that hands the raw oneOf to a
    structural validator sees *every* string match *both* branches and rejects
    every value. A reference to a valid target must pass.
    """

    config = Config("x-gts-ref: oneOf shared structural keywords").base_url(
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
        # oneOf branches share `type: string` and differ only by x-gts-ref.
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
                            {"type": "string", "x-gts-ref": "gts.x.testref_shared._.target_a.v1~"},
                            {"type": "string", "x-gts-ref": "gts.x.testref_shared._.target_b.v1~"},
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


class TestCaseXGtsRef_ImplicitObjectAndLocalRef(HttpRunner):
    config = Config("x-gts-ref: implicit object and local refs").base_url(
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
            RunRequest("register implicit object x-gts-ref schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_implicit._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "required": ["id", "ref"],
                "properties": {
                    "id": {"type": "string"},
                    "ref": {
                        "type": "string",
                        "x-gts-ref": "gts.x.testref_implicit._.target.v1~",
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
            RunRequest("register local ref x-gts-ref schema")
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
                        "x-gts-ref": "gts.x.testref_local._.target.v1~",
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
    config = Config("x-gts-ref: local ref missing target").base_url(get_gts_base_url())

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
                        "x-gts-ref": "gts.x.testref_local_missing._.target.v1~",
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
    config = Config("x-gts-ref: annotation data is not a subschema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with x-gts-ref-shaped annotation data")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_annotation._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "payload": {
                        "type": "object",
                        "default": {"x-gts-ref": "not-a-gts-id"},
                        "const": {
                            "x-gts-ref": "gts.x.testref_annotation._.missing.v1~"
                        },
                        "examples": [{"x-gts-ref": 42}],
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_annotation._.holder.v1~",
            True,
            "accept x-gts-ref-shaped values in annotation data",
        ),
    ]


class TestCaseXGtsRef_PropertyNamedKeyword(HttpRunner):
    config = Config("x-gts-ref: property named like the keyword").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with a property named x-gts-ref")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_property_name._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "x-gts-ref": {
                        "type": "string",
                        "x-gts-ref": "gts.x.testref_property_name._.missing.v1~",
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        _validate_type_schema(
            "gts.x.testref_property_name._.holder.v1~",
            False,
            "reject missing target under a property named x-gts-ref",
        ),
    ]


class TestCaseXGtsRef_RootLocalReference(HttpRunner):
    """A bare ``$ref: "#"`` must traverse the complete root schema.

    Existing local-reference coverage uses ``#/...`` pointers into a
    subschema. This case is distinct: a recursive child points to the root
    document itself, and the nested ``x-gts-ref`` must still be validated.
    """
    config = Config("x-gts-ref: root local reference").base_url(get_gts_base_url())

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
                        "x-gts-ref": "gts.x.testref_root._.target.v1~",
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
    """x-gts-ref: arbitrary wildcard patterns (not just ``gts.*``).

    §9.6: the constraint value may be any well-formed GTS wildcard pattern
    (§10), e.g. ``gts.x.testref_wild.am.*``. The field value must be a
    syntactically valid GTS id that matches the pattern. Registry presence and
    target validity then follow the selected gts-ref-validation mode.
    """
    config = Config("x-gts-ref: arbitrary wildcard pattern").base_url(get_gts_base_url())

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
            RunRequest("register holder schema with wildcard x-gts-ref")
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
                        "x-gts-ref": "gts.x.testref_wild.am.*",
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
    """x-gts-ref: ``...v1~*`` wildcard covers the base type and its descendants.

    Per §3.5/§10, ``gts....stream.v1~*`` matches the type ``...stream.v1~``
    itself as well as any entity derived from it. Registry lookup and target
    validity follow the selected gts-ref-validation mode.
    """
    config = Config("x-gts-ref: tilde wildcard pattern").base_url(get_gts_base_url())

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
            RunRequest("register holder schema with tilde wildcard x-gts-ref")
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
                        "x-gts-ref": "gts.x.testref_wild.events.stream.v1~*",
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
    config = Config("x-gts-ref: referenced instance validation modes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register x-gts-ref target type")
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
            RunRequest("register invalid x-gts-ref target instance")
            .post("/entities")
            .with_json({
                "id": "gts.x.testref_validity._.target.v1~x.vendor._.invalid.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate x-gts-ref target instance")
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
            RunRequest("register x-gts-ref holder type")
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
                        "x-gts-ref": "gts.x.testref_validity._.target.v1~",
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
    config = Config("x-gts-ref: constraint validation modes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register invalid x-gts-ref constraint type")
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
            RunRequest("register holder using invalid x-gts-ref constraint type")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testref_constraint._.holder.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "x-gts-ref": "gts.x.testref_constraint._.target.v1~",
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
    config = Config("x-gts-ref wildcard validation modes").base_url(
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
                        "x-gts-ref": "gts.x.testref_wildpresence.empty.*",
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
                        "x-gts-ref": "gts.x.testref_wildvalidity.target.*",
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
    config = Config("x-gts-ref registration validation modes").base_url(
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
                        "x-gts-ref": "gts.x.testref_regmode._.missing.v1~",
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
                        "x-gts-ref": "gts.x.testref_regmode._.missing.v1~",
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
                        "x-gts-ref": "gts.x.testref_regmode._.target.v1~",
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
                        "x-gts-ref": "gts.x.testref_regmode._.target.v1~",
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
    config = Config("x-gts-ref: Draft-07 tuple additionalItems").base_url(
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
                            "x-gts-ref": "gts.x.testref_tuple._.target.v1~",
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
                    "x-gts-ref": "gts.x.testref_tuple._.missing_target.v1~",
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
    config = Config("x-gts-ref: Draft 2020-12 prefixItems").base_url(
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
                            "x-gts-ref": "gts.x.testref_prefixitems._.target.v1~",
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
    """x-gts-ref: nullable reference via a combinator with a neutral branch.

    The common "optional reference" shape mixes an x-gts-ref branch with a
    plain structural branch that carries no x-gts-ref, e.g.::

        "oneOf": [
            {"type": "string", "x-gts-ref": "gts.a._.b.v1~"},
            {"type": "null"}
        ]

    The neutral ``{"type": "null"}`` branch has no x-gts-ref, so the standard
    JSON Schema engine already enforces which branch a value belongs to. An
    implementation that runs its own x-gts-ref combinator pass must treat a
    branch without an x-gts-ref as neutral rather than a branch that always
    "matches"; otherwise a valid string reference counts as matching *both*
    branches and a valid value is rejected. Earlier combinator coverage only
    exercised combinators where *every* branch carried an x-gts-ref, so this
    mixed shape was never checked.
    """

    config = Config("x-gts-ref: nullable reference").base_url(get_gts_base_url())

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
        # oneOf: nullable reference (string+x-gts-ref OR null).
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
                                "x-gts-ref": "gts.x.testref_nullable._.target.v1~",
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
        # A valid string reference must match exactly the x-gts-ref branch.
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
        # anyOf: nullable reference (string+x-gts-ref OR null).
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
                                "x-gts-ref": "gts.x.testref_nullable._.target.v1~",
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
    """x-gts-ref: a /$id branch inside oneOf must not shadow a sibling branch.

    ``oneOf`` requires exactly one branch to match. When one branch is
    ``{"x-gts-ref": "/$id"}`` and another is a concrete GTS pattern, an
    implementation must resolve ``/$id`` to the selected type while selecting
    the matching branch. If ``/$id`` is instead treated as always-matching
    (e.g. a JSON Schema engine that evaluates x-gts-ref as a keyword but
    short-circuits ``/$id`` to "valid" because it lacks the selected type),
    a value that matches only the sibling pattern satisfies *both* branches
    and the exactly-one rule wrongly rejects a valid value.

    Prior oneOf coverage only used concrete patterns in every branch, so this
    /$id-versus-concrete combination was never exercised.
    """

    config = Config("x-gts-ref: /$$id inside oneOf").base_url(get_gts_base_url())

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
                            {"x-gts-ref": "/$$id"},
                            {"x-gts-ref": "gts.x.testref_selfcomb._.other.v1~"},
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


if __name__ == "__main__":
    TestCaseXGtsRef_PrefixAndSelfRef().test_start()
    TestCaseXGtsRef_UnsupportedPointers().test_start()
    TestCaseXGtsRef_SelectedLeafSelfRef().test_start()
    TestCaseXGtsRef_WrongGtsFormat().test_start()
    TestCaseXGtsRef_OneOf().test_start()
    TestCaseXGtsRef_AnyOf().test_start()
    TestCaseXGtsRef_AllOf().test_start()
    TestCaseXGtsRef_NestedCombinators().test_start()
    TestCaseXGtsRef_WildcardPattern().test_start()
    TestCaseXGtsRef_TildeWildcardPattern().test_start()
    TestCaseXGtsRef_NullableReference().test_start()
    TestCaseXGtsRef_SelfRefInOneOf().test_start()
