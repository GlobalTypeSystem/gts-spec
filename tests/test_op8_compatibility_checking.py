import pytest

from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


# Helper function to create base schema registration step
def register_base_schema():
    return Step(
        RunRequest("register base schema")
        .post("/entities")
        .with_json({
            "$$id": "gts://gts.x.test8.compat.base.v1~",
            "$$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["eventId", "timestamp"],
            "properties": {
                "eventId": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"}
            }
        })
        .validate()
        .assert_equal("status_code", 200)
    )


class TestCaseTestOp8Compatibility_BackwardCompatible(HttpRunner):
    """OP#8.1 - Backward Compatibility: Removing optional field from open model"""
    config = Config("OP#8 - Backward Compatible (remove optional, open)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        register_base_schema(),
        # Register v1.0 schema
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.event.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "timestamp", "userId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "userId": {"type": "string"},
                    "metadata": {"type": "object"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (removes optional field from an open model)
        Step(
            RunRequest("register v1.1 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.event.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "timestamp", "userId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "userId": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility: v1.0 -> v1.1
        Step(
            RunRequest("check backward compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.event.v1.0~",
                    "new_type_id": "gts.x.test8.compat.event.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
            .assert_equal("body.old", "gts.x.test8.compat.event.v1.0~")
            .assert_equal("body.new", "gts.x.test8.compat.event.v1.1~")
        ),
    ]


class TestCaseTestOp8Compatibility_BackwardIncompatible(HttpRunner):
    """OP#8.1 - Backward Incompatible: Adding required field"""
    config = Config("OP#8 - Backward Incompatible (add required)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.breaking.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (adds required field - breaking!)
        Step(
            RunRequest("register v1.1 schema with new required field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.breaking.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "newRequiredField"],
                "properties": {
                    "eventId": {"type": "string"},
                    "newRequiredField": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility: should NOT be backward compatible
        Step(
            RunRequest("check backward incompatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.breaking.v1.0~",
                    "new_type_id": "gts.x.test8.compat.breaking.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ForwardCompatible(HttpRunner):
    """OP#8.2 - Forward Compatibility: Adding optional field to open model"""
    config = Config("OP#8 - Forward Compatible (add optional, open)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema with additionalProperties: true
        Step(
            RunRequest("register v1.0 schema (open model)")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.forward.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": True
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (adds an optional property schema)
        Step(
            RunRequest("register v1.1 schema with new field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.forward.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "newField": {"type": "string"}
                },
                "additionalProperties": True
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility: should be forward compatible
        Step(
            RunRequest("check forward compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.forward.v1.0~",
                    "new_type_id": "gts.x.test8.compat.forward.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ForwardIncompatible(HttpRunner):
    """OP#8.2 - Forward Incompatible: Removing required field"""
    config = Config("OP#8 - Forward Incompatible (remove required)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.fwd_break.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "importantField"],
                "properties": {
                    "eventId": {"type": "string"},
                    "importantField": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (removes required field)
        Step(
            RunRequest("register v1.1 schema without required field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.fwd_break.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility: should NOT be forward compatible
        Step(
            RunRequest("check forward incompatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.fwd_break.v1.0~",
                    "new_type_id": "gts.x.test8.compat.fwd_break.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_FullyCompatible(HttpRunner):
    """OP#8.3 - Full Compatibility: Annotation-only changes"""
    config = Config("OP#8 - Fully Compatible (annotations only)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.full.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {
                        "type": "string",
                        "description": "Event identifier"
                    }
                },
                "additionalProperties": True
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (changes annotations only)
        Step(
            RunRequest("register v1.1 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.full.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {
                        "type": "string",
                        "description": "Stable event identifier",
                        "examples": ["evt-123"]
                    }
                },
                "additionalProperties": True
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility: should be fully compatible
        Step(
            RunRequest("check full compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.full.v1.0~",
                    "new_type_id": "gts.x.test8.compat.full.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "compatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ClosedModelAddOptional(HttpRunner):
    """OP#8 - Closed model: Adding optional property is backward only"""
    config = Config("OP#8 - Add optional (closed model)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema (closed model)
        Step(
            RunRequest("register v1.0 closed schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closed_add.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (adds an optional property, still closed)
        Step(
            RunRequest("register v1.1 closed schema with optional property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closed_add.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "label": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # v1.1 accepts every v1.0 instance; v1.0 rejects the new property
        Step(
            RunRequest("check closed model add optional compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.closed_add.v1.0~",
                    "new_type_id": "gts.x.test8.compat.closed_add.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ClosedModelRemoveOptional(HttpRunner):
    """OP#8 - Closed model: Removing optional property is forward only"""
    config = Config("OP#8 - Remove optional (closed model)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema (closed model with an optional property)
        Step(
            RunRequest("register v1.0 closed schema with optional property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closed_remove.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "label": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (removes the optional property, still closed)
        Step(
            RunRequest("register v1.1 closed schema without optional property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closed_remove.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # v1.0 accepts every v1.1 instance; v1.1 rejects old data with `label`
        Step(
            RunRequest("check closed model remove optional compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.closed_remove.v1.0~",
                    "new_type_id": "gts.x.test8.compat.closed_remove.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_TypeChange(HttpRunner):
    """OP#8 - Incompatible: Changing field type"""
    config = Config("OP#8 - Type Change (incompatible)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.typechange.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "count"],
                "properties": {
                    "eventId": {"type": "string"},
                    "count": {"type": "number"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (changes count type from number to string)
        Step(
            RunRequest("register v1.1 schema with type change")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.typechange.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "count"],
                "properties": {
                    "eventId": {"type": "string"},
                    "count": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility: should be incompatible both ways
        Step(
            RunRequest("check incompatibility due to type change")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.typechange.v1.0~",
                    "new_type_id": "gts.x.test8.compat.typechange.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_EnumExpansion(HttpRunner):
    """OP#8 - Enum Expansion: Backward compatible, not forward"""
    config = Config("OP#8 - Enum Expansion").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema with enum
        Step(
            RunRequest("register v1.0 schema with enum")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.enum.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "status"],
                "properties": {
                    "eventId": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive"]
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (adds enum value)
        Step(
            RunRequest("register v1.1 schema with expanded enum")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.enum.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "status"],
                "properties": {
                    "eventId": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"]
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility: backward compatible, not forward
        Step(
            RunRequest("check enum expansion compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.enum.v1.0~",
                    "new_type_id": "gts.x.test8.compat.enum.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_EnumReduction(HttpRunner):
    """OP#8 - Enum Reduction: Forward compatible, not backward"""
    config = Config("OP#8 - Enum Reduction").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 schema with enum")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.enum_reduction.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "status"],
                "properties": {
                    "eventId": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"]
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 schema with reduced enum")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.enum_reduction.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "status"],
                "properties": {
                    "eventId": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive"]
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check enum reduction compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": (
                        "gts.x.test8.compat.enum_reduction.v1.0~"
                    ),
                    "new_type_id": (
                        "gts.x.test8.compat.enum_reduction.v1.1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]




class TestCaseTestOp8Compatibility_NestedObjectChanges(HttpRunner):
    """Test compatibility with nested object modifications"""
    config = Config("OP#8 Extended - Nested Object Compatibility").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 with nested object
        Step(
            RunRequest("register v1.0 with nested object")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.nested_compat.order.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["orderId", "customer"],
                "properties": {
                    "orderId": {"type": "string"},
                    "customer": {
                        "type": "object",
                        "required": ["customerId", "name"],
                        "properties": {
                            "customerId": {"type": "string"},
                            "name": {"type": "string"}
                        }
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 with additional nested field
        Step(
            RunRequest("register v1.1 with additional nested field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.nested_compat.order.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["orderId", "customer"],
                "properties": {
                    "orderId": {"type": "string"},
                    "customer": {
                        "type": "object",
                        "required": ["customerId", "name"],
                        "properties": {
                            "customerId": {"type": "string"},
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        }
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility
        Step(
            RunRequest("check nested object compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": (
                        "gts.x.test8.nested_compat.order.v1.0~"
                    ),
                    "new_type_id": (
                        "gts.x.test8.nested_compat.order.v1.1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ConstraintRelaxation(HttpRunner):
    """Test compatibility when relaxing constraints"""
    config = Config("OP#8 Extended - Constraint Relaxation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 with strict constraints
        Step(
            RunRequest("register v1.0 with strict constraints")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.constraints.product.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["productId", "price"],
                "properties": {
                    "productId": {"type": "string"},
                    "price": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1000
                    },
                    "name": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 50
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 with relaxed constraints
        Step(
            RunRequest("register v1.1 with relaxed constraints")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.constraints.product.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["productId", "price"],
                "properties": {
                    "productId": {"type": "string"},
                    "price": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 10000
                    },
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 100
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility - should be backward compatible
        Step(
            RunRequest("check constraint relaxation compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": (
                        "gts.x.test8.constraints.product.v1.0~"
                    ),
                    "new_type_id": (
                        "gts.x.test8.constraints.product.v1.1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ConstraintTightening(HttpRunner):
    """Test compatibility when tightening constraints"""
    config = Config("OP#8 Extended - Constraint Tightening").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 with loose constraints
        Step(
            RunRequest("register v1.0 with loose constraints")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.tight.item.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["itemId", "quantity"],
                "properties": {
                    "itemId": {"type": "string"},
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 1000
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 with tighter constraints
        Step(
            RunRequest("register v1.1 with tighter constraints")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.tight.item.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["itemId", "quantity"],
                "properties": {
                    "itemId": {"type": "string"},
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility - should NOT be backward compatible
        Step(
            RunRequest("check constraint tightening compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.tight.item.v1.0~",
                    "new_type_id": "gts.x.test8.tight.item.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ArrayItemSchemaChange(HttpRunner):
    """Test compatibility with array item schema changes"""
    config = Config("OP#8 Extended - Array Item Schema Changes").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 with simple array items
        Step(
            RunRequest("register v1.0 with simple array items")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.array_compat.list.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["listId", "items"],
                "properties": {
                    "listId": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "value"],
                            "properties": {
                                "id": {"type": "string"},
                                "value": {"type": "number"}
                            }
                        }
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 with additional array item field
        Step(
            RunRequest("register v1.1 with additional array item field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.array_compat.list.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["listId", "items"],
                "properties": {
                    "listId": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "value"],
                            "properties": {
                                "id": {"type": "string"},
                                "value": {"type": "number"},
                                "label": {"type": "string"}
                            }
                        }
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Check compatibility
        Step(
            RunRequest("check array item schema compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": (
                        "gts.x.test8.array_compat.list.v1.0~"
                    ),
                    "new_type_id": (
                        "gts.x.test8.array_compat.list.v1.1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_RemoveRequiredClosedModel(HttpRunner):
    """OP#8 - Closed model: Removing a required property definition is neither

    Spec 0.13 §4.5, row "Removing required property definition (closed model)".
    The new closed schema rejects old instances that carry the property, and
    the old schema rejects new instances that omit it.
    """
    config = Config("OP#8 - Remove required (closed model)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 closed schema with required property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closed_req.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "importantField"],
                "properties": {
                    "eventId": {"type": "string"},
                    "importantField": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 closed schema without the property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closed_req.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check closed model remove required compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.closed_req.v1.0~",
                    "new_type_id": "gts.x.test8.compat.closed_req.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ClosingOpenObject(HttpRunner):
    """OP#8 - Content model: Closing an open object is forward only

    Spec 0.13 §4.5, row "Closing an open object". The new schema rejects the
    undeclared properties an old instance may carry; every new instance stays
    valid under the more permissive old schema.
    """
    config = Config("OP#8 - Close an open object").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 open schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closing.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": True
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 closed schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.closing.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check open to closed compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.closing.v1.0~",
                    "new_type_id": "gts.x.test8.compat.closing.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_OpeningClosedObject(HttpRunner):
    """OP#8 - Content model: Opening a closed object is backward only

    Spec 0.13 §4.5, row "Opening a closed object". The new schema accepts every
    old instance; the old closed schema rejects new instances that carry an
    undeclared property.
    """
    config = Config("OP#8 - Open a closed object").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 closed schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.opening.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 open schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.opening.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"}
                },
                "additionalProperties": True
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check closed to open compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.opening.v1.0~",
                    "new_type_id": "gts.x.test8.compat.opening.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ConstIdentityChange(HttpRunner):
    """OP#8 - Changing a `const` value on a required property is neither

    Spec 0.13 §4.5, row "Changing a `const` value", and §4.6.3. The two `const`
    values differ, so the schemas share no valid instance. OP#9 casting may
    rewrite such a field, but that is reported separately.
    """
    config = Config("OP#8 - Const identity change").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 schema with const identity field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.const_id.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "kind"],
                "properties": {
                    "eventId": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "const": "gts.x.test8.compat.const_id.v1.0~"
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 schema with changed const value")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.const_id.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "kind"],
                "properties": {
                    "eventId": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "const": "gts.x.test8.compat.const_id.v1.1~"
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check const change compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.const_id.v1.0~",
                    "new_type_id": "gts.x.test8.compat.const_id.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_RenameProperty(HttpRunner):
    """OP#8 - Renaming a required property is neither

    Spec 0.13 §4.5, row "Renaming property": equivalent to remove + add.
    """
    config = Config("OP#8 - Rename property").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.rename.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "userId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "userId": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 schema with the property renamed")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.rename.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "accountId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "accountId": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check rename compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.rename.v1.0~",
                    "new_type_id": "gts.x.test8.compat.rename.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_NumericWidening(HttpRunner):
    """OP#8 - Widening a numeric type (integer -> number) is backward only

    Spec 0.13 §4.5, row "Widening numeric type". Every integer stays valid; the
    old schema rejects the non-integer values the new schema now admits.
    """
    config = Config("OP#8 - Numeric widening (int -> number)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 schema with integer property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.widen.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "amount"],
                "properties": {
                    "eventId": {"type": "string"},
                    "amount": {"type": "integer"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 schema with number property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.widen.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "amount"],
                "properties": {
                    "eventId": {"type": "string"},
                    "amount": {"type": "number"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check numeric widening compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.widen.v1.0~",
                    "new_type_id": "gts.x.test8.compat.widen.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_NumericNarrowing(HttpRunner):
    """OP#8 - Narrowing a numeric type (number -> integer) is forward only

    Spec 0.13 §4.5, row "Narrowing numeric type". The old schema accepts every
    integer; the new schema rejects the non-integer values the old one admitted.
    """
    config = Config("OP#8 - Numeric narrowing (number -> int)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register v1.0 schema with number property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.narrow.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "amount"],
                "properties": {
                    "eventId": {"type": "string"},
                    "amount": {"type": "number"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 schema with integer property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.narrow.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "amount"],
                "properties": {
                    "eventId": {"type": "string"},
                    "amount": {"type": "integer"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check numeric narrowing compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.narrow.v1.0~",
                    "new_type_id": "gts.x.test8.compat.narrow.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ReferencedTypeWidened(HttpRunner):
    """OP#8 - Updating a referenced GTS type: widened target is backward only

    Spec 0.13 §4.5, row "Updating a referenced GTS type": the verdict follows
    from the effective resolved schemas. Here the container is unchanged apart
    from the reference, and the new target accepts strictly more instances, so
    the containing schema is backward compatible and not forward compatible.
    """
    config = Config("OP#8 - Referenced type widened").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register referenced target v1.0")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.target.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {"type": "string", "enum": ["a", "b"]}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register referenced target v1.1 with a wider enum")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.target.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {"type": "string", "enum": ["a", "b", "c"]}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register container v1.0 referencing target v1.0")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.container.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "detail"],
                "properties": {
                    "eventId": {"type": "string"},
                    "detail": {
                        "$$ref": "gts://gts.x.test8.compat.target.v1.0~"
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register container v1.1 referencing target v1.1")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.container.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "detail"],
                "properties": {
                    "eventId": {"type": "string"},
                    "detail": {
                        "$$ref": "gts://gts.x.test8.compat.target.v1.1~"
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check referenced type update compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.container.v1.0~",
                    "new_type_id": "gts.x.test8.compat.container.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "incompatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_TypeLessObjectConstraints(HttpRunner):
    """OP#8 - Object keywords constrain type-less schemas.

    JSON Schema applies `required` and `properties` to object instances even
    when `type` is omitted. Adding a required property therefore makes the new
    schema reject an object accepted by the old schema.
    """
    config = Config("OP#8 - Type-less Object Constraints").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register type-less v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.typeless.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "required": ["eventId"],
                "properties": {"eventId": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register type-less v1.1 schema with required field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.typeless.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "required": ["eventId", "source"],
                "properties": {
                    "eventId": {"type": "string"},
                    "source": {"type": "string"},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # The new required property rejects old object instances without source.
        Step(
            RunRequest("check type-less object compatibility")
            .get("/compatibility")
            .with_params(**{
                "old_type_id": "gts.x.test8.compat.typeless.v1.0~",
                "new_type_id": "gts.x.test8.compat.typeless.v1.1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_TypeLessArrayConstraints(HttpRunner):
    """OP#8 - Array keywords constrain type-less schemas.

    JSON Schema applies `items` to array instances even when `type` is omitted.
    Tightening the item schema therefore rejects old arrays that contain a value
    accepted by the old schema.
    """
    config = Config("OP#8 - Type-less Array Constraints").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register type-less v1.0 array schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.typeless_array.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "items": {"type": "string"},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register type-less v1.1 array schema with max length")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.typeless_array.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "items": {"type": "string", "maxLength": 10},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # The new item constraint rejects old arrays containing longer strings.
        Step(
            RunRequest("check type-less array compatibility")
            .get("/compatibility")
            .with_params(**{
                "old_type_id": "gts.x.test8.compat.typeless_array.v1.0~",
                "new_type_id": "gts.x.test8.compat.typeless_array.v1.1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_EquivalentDialectSpellings(HttpRunner):
    config = Config("OP#8 - Equivalent Dialect Spellings").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register http Draft-07 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.dialect_equivalent.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "string",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register https Draft-07 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.dialect_equivalent.v1.1~",
                "$$schema": "https://json-schema.org/draft-07/schema",
                "type": "string",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check equivalent dialect compatibility")
            .get("/compatibility")
            .with_params(**{
                "old_type_id": "gts.x.test8.compat.dialect_equivalent.v1.0~",
                "new_type_id": "gts.x.test8.compat.dialect_equivalent.v1.1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "compatible")
        ),
    ]


class TestCaseTestOp8Compatibility_DistinctDialects(HttpRunner):
    config = Config("OP#8 - Distinct Dialects").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register Draft-07 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.dialect_changed.v1.0~",
                "$$schema": "https://json-schema.org/draft-07/schema",
                "type": "string",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register Draft 2020-12 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.dialect_changed.v1.1~",
                "$$schema": "http://json-schema.org/draft/2020-12/schema#",
                "type": "string",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check distinct dialect compatibility")
            .get("/compatibility")
            .with_params(**{
                "old_type_id": "gts.x.test8.compat.dialect_changed.v1.0~",
                "new_type_id": "gts.x.test8.compat.dialect_changed.v1.1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "unknown")
            .assert_equal("body.forward_compatibility", "unknown")
            .assert_equal("body.full_compatibility", "unknown")
        ),
    ]


class TestCaseTestOp8Compatibility_Draft202012UnevaluatedProperties(HttpRunner):
    config = Config("OP#8 - Draft 2020-12 unevaluatedProperties").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register open Draft 2020-12 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.unevaluated.v1.0~",
                "$$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register closed Draft 2020-12 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.unevaluated.v1.1~",
                "$$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "unevaluatedProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check Draft 2020-12 content model compatibility")
            .get("/compatibility")
            .with_params(**{
                "old_type_id": "gts.x.test8.compat.unevaluated.v1.0~",
                "new_type_id": "gts.x.test8.compat.unevaluated.v1.1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "incompatible")
        ),
    ]


class TestCaseTestOp8Compatibility_ConditionalUnevaluatedProperties(HttpRunner):
    """Conditional applicators must not be lowered to ``additionalProperties``.

    The source (v1.0) accepts ``{}`` and ``{"value": <string>}``; the target
    (v1.1) accepts only ``{}``, so the target's accepted-instance set is a
    strict subset of the source's. Per §4.3 the definitive verdicts are
    backward ``incompatible``, forward ``compatible``, full ``incompatible``.

    An implementation that mechanically lowers ``unevaluatedProperties`` to
    ``additionalProperties: false`` would compute the source's set incorrectly
    and reach a wrong verdict. README §4.3/§9.2 allow ``unknown`` when the
    checker cannot establish a relation, but do not require it here. This test
    therefore accepts either the correct definitive verdict or ``unknown`` for
    each relation, so a checker that solves the conditional case is not
    rejected.
    """
    config = Config("OP#8 - Conditional unevaluatedProperties").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register conditional source schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.conditional.v1.0~",
                "$$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "if": {"required": ["value"]},
                "then": {"properties": {"value": {"type": "string"}}},
                "unevaluatedProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register closed target schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.conditional.v1.1~",
                "$$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check conditional unevaluatedProperties compatibility")
            .get("/compatibility")
            .with_params(**{
                "old_type_id": "gts.x.test8.compat.conditional.v1.0~",
                "new_type_id": "gts.x.test8.compat.conditional.v1.1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_contained_by("body.backward_compatibility", ["incompatible", "unknown"])
            .assert_contained_by("body.forward_compatibility", ["compatible", "unknown"])
            .assert_contained_by("body.full_compatibility", ["incompatible", "unknown"])
        ),
    ]


class TestCaseTestOp8Compatibility_IdentityFullyCompatible(HttpRunner):
    """OP#8 - Identity baseline: two structurally identical schemas.

    Anchors the compatibility matrix: when the new schema is byte-for-byte the
    same shape as the old one, every instance is mutually valid, so all three
    verdicts MUST be ``compatible``.
    """
    config = Config("OP#8 - Identity (fully compatible)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    _SCHEMA_BODY = {
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["eventId", "count"],
        "properties": {
            "eventId": {"type": "string"},
            "count": {"type": "integer", "minimum": 0},
            "label": {"type": "string"},
        },
        "additionalProperties": False,
    }

    teststeps = [
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.identity.v1.0~",
                **_SCHEMA_BODY,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register v1.1 identical schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.identity.v1.1~",
                **_SCHEMA_BODY,
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check identity compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.compat.identity.v1.0~",
                    "new_type_id": "gts.x.test8.compat.identity.v1.1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "compatible")
            .assert_equal("body.forward_compatibility", "compatible")
            .assert_equal("body.full_compatibility", "compatible")
        ),
    ]


_PATTERN_RESOURCE = "gts.x.core.resources.resource.v1~"
_PATTERN_FAMILY = "gts.x.core.resources.resource.*"
_PATTERN_INSTANCE = _PATTERN_RESOURCE + "acme.prod._.uploads.v1"


def _check_compatibility(
    api, old_type, new_type, expected_verdicts, unknown_allowed=False
):
    result = api.request(
        "GET",
        "/compatibility",
        params={"old_type_id": old_type, "new_type_id": new_type},
    )
    for relation, verdict in expected_verdicts.items():
        accepted = {verdict, "unknown"} if unknown_allowed else {verdict}
        assert result[relation + "_compatibility"] in accepted, result


@pytest.mark.parametrize(
    "old_scope_schema,new_scope_schema,expected_verdicts,unknown_allowed",
    [
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
            {"type": "string", "x-gts-pattern-ref": _PATTERN_FAMILY},
            {
                "backward": "compatible",
                "forward": "incompatible",
                "full": "incompatible",
            },
            False,
            id="pattern_widening",
        ),
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": _PATTERN_FAMILY},
            {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
            {
                "backward": "incompatible",
                "forward": "compatible",
                "full": "incompatible",
            },
            False,
            id="pattern_narrowing",
        ),
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
            {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE + "*"},
            {"backward": "compatible", "forward": "compatible", "full": "compatible"},
            False,
            id="pattern_equivalent_scopes",
        ),
        pytest.param(
            {"not": {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE}},
            {"not": {"type": "string", "x-gts-pattern-ref": _PATTERN_FAMILY}},
            {
                "backward": "incompatible",
                "forward": "compatible",
                "full": "incompatible",
            },
            False,
            id="pattern_negated_widening",
        ),
        pytest.param(
            {"not": {"type": "string", "x-gts-pattern-ref": _PATTERN_FAMILY}},
            {"not": {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE}},
            {
                "backward": "compatible",
                "forward": "incompatible",
                "full": "incompatible",
            },
            False,
            id="pattern_negated_narrowing",
        ),
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
            {"type": "string", "x-gts-pattern-ref": "gts.x.core.resources.resource.v1.*"},
            {"backward": "incompatible", "forward": "compatible", "full": "incompatible"},
            False,
            id="pattern_minor_wildcard_narrowing",
        ),
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": "gts.x.core.resources.resource.v1.*"},
            {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
            {"backward": "compatible", "forward": "incompatible", "full": "incompatible"},
            False,
            id="pattern_minor_wildcard_widening",
        ),
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": _PATTERN_INSTANCE},
            {"type": "string", "x-gts-pattern-ref": _PATTERN_INSTANCE + ".0"},
            {"backward": "incompatible", "forward": "compatible", "full": "incompatible"},
            False,
            id="pattern_instance_minor_narrowing",
        ),
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": _PATTERN_INSTANCE + ".0"},
            {"type": "string", "x-gts-pattern-ref": _PATTERN_INSTANCE},
            {"backward": "compatible", "forward": "incompatible", "full": "incompatible"},
            False,
            id="pattern_instance_minor_widening",
        ),
        pytest.param(
            {"type": "string", "x-gts-pattern-ref": _PATTERN_INSTANCE},
            {
                "type": "string",
                "x-gts-pattern-ref": _PATTERN_INSTANCE.replace("v1~", "v1.0~"),
            },
            {"backward": "incompatible", "forward": "compatible", "full": "incompatible"},
            False,
            id="pattern_instance_type_minor_narrowing",
        ),
        pytest.param(
            {
                "type": "string",
                "x-gts-pattern-ref": _PATTERN_INSTANCE.replace("v1~", "v1.0~"),
            },
            {"type": "string", "x-gts-pattern-ref": _PATTERN_INSTANCE},
            {"backward": "compatible", "forward": "incompatible", "full": "incompatible"},
            False,
            id="pattern_instance_type_minor_widening",
        ),
        # Compositions are assessed as a whole and may be reported `unknown`.
        pytest.param(
            {
                "allOf": [
                    {"type": "string", "x-gts-pattern-ref": _PATTERN_FAMILY},
                    {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
                ]
            },
            {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
            {"backward": "compatible", "forward": "compatible", "full": "compatible"},
            True,
            id="pattern_intersection",
        ),
        pytest.param(
            {
                "allOf": [
                    {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
                    {"type": "string", "x-gts-pattern-ref": _PATTERN_FAMILY},
                ]
            },
            {
                "allOf": [
                    {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
                    {"type": "string", "x-gts-pattern-ref": "gts.*"},
                ]
            },
            {"backward": "compatible", "forward": "compatible", "full": "compatible"},
            True,
            id="pattern_masked_widening",
        ),
    ],
)
def test_pattern_ref_evolution(
    gts_api,
    schema_dialect,
    old_scope_schema,
    new_scope_schema,
    expected_verdicts,
    unknown_allowed,
):
    """Isolated and negated scopes have definite verdicts (README §9.6.2).

    A composition is assessed as a whole and may be reported ``unknown`` when
    inclusion cannot be established, but never with the wrong definite verdict.
    """
    api = gts_api
    old_type = api.register(
        "old",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": old_scope_schema},
        },
        schema_dialect,
        type_id=api.type_id("evolution", "1.0"),
    )
    new_type = api.register(
        "new",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {"scope": new_scope_schema},
        },
        schema_dialect,
        type_id=api.type_id("evolution", "1.1"),
    )
    _check_compatibility(api, old_type, new_type, expected_verdicts, unknown_allowed)


@pytest.mark.parametrize(
    "old_operand,new_operand,expected_verdicts",
    [
        # The v1.0 and v1.1 roots select disjoint scopes.
        pytest.param(
            "/$id",
            "/$id",
            {
                "backward": "incompatible",
                "forward": "incompatible",
                "full": "incompatible",
            },
            id="both_self",
        ),
        pytest.param(
            "new_type_id",
            "/$id",
            {"backward": "compatible", "forward": "compatible", "full": "compatible"},
            id="new_self_equals_literal",
        ),
        pytest.param(
            "/$id",
            "old_type_id",
            {"backward": "compatible", "forward": "compatible", "full": "compatible"},
            id="old_self_equals_literal",
        ),
    ],
)
def test_pattern_ref_evolution_resolves_each_self_reference(
    gts_api, schema_dialect, old_operand, new_operand, expected_verdicts
):
    """`/$id` names the schema it is resolved for, on each side."""
    api = gts_api
    type_ids = {
        "old_type_id": api.type_id("self", "1.0"),
        "new_type_id": api.type_id("self", "1.1"),
    }
    old_type = api.register(
        "old",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "type": "string",
                    "x-gts-pattern-ref": type_ids.get(old_operand, old_operand),
                },
            },
        },
        schema_dialect,
        type_id=type_ids["old_type_id"],
    )
    new_type = api.register(
        "new",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "type": "string",
                    "x-gts-pattern-ref": type_ids.get(new_operand, new_operand),
                },
            },
        },
        schema_dialect,
        type_id=type_ids["new_type_id"],
    )
    _check_compatibility(api, old_type, new_type, expected_verdicts)


def test_pattern_ref_conditional_evolution_preserves_inconclusive_verdicts(
    gts_api, schema_dialect
):
    """The old `if`/`then`/`else` scope accepts all of FAMILY; the new one only
    RESOURCE. A solver may prove the relation or return unknown, never the
    opposite."""
    api = gts_api
    old_type = api.register(
        "old",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {
                    "if": {"const": _PATTERN_RESOURCE},
                    "then": {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
                    "else": {"type": "string", "x-gts-pattern-ref": _PATTERN_FAMILY},
                },
            },
        },
        schema_dialect,
        type_id=api.type_id("conditional", "1.0"),
    )
    new_type = api.register(
        "new",
        {
            "type": "object",
            "required": ["scope"],
            "properties": {
                "scope": {"type": "string", "x-gts-pattern-ref": _PATTERN_RESOURCE},
            },
        },
        schema_dialect,
        type_id=api.type_id("conditional", "1.1"),
    )
    _check_compatibility(
        api,
        old_type,
        new_type,
        {"backward": "incompatible", "forward": "compatible", "full": "incompatible"},
        unknown_allowed=True,
    )



# ---------------------------------------------------------------------------
# x-gts-type-ref / x-gts-instance-ref evolution (README §9.6.1, ADR-0008)
# ---------------------------------------------------------------------------

_TYPE_REF = "x-gts-type-ref"
_INSTANCE_REF = "x-gts-instance-ref"
_COMPATIBLE = {"backward": "compatible", "forward": "compatible", "full": "compatible"}
_INCOMPATIBLE = {
    "backward": "incompatible",
    "forward": "incompatible",
    "full": "incompatible",
}
_WIDENING = {"backward": "compatible", "forward": "incompatible", "full": "incompatible"}
_NARROWING = {"backward": "incompatible", "forward": "compatible", "full": "incompatible"}


def _entity_ref_operands(api, dialect):
    """Registered, valid operand targets, so no policy affects either schema."""
    target = api.register("target", {"type": "object"}, dialect)
    derived = api.register(
        "derived",
        {"type": "object", "allOf": [{"$ref": "gts://" + target}]},
        dialect,
        type_id=api.derived_type_id(target, "derived"),
    )
    pinned = api.register(
        "target", {"type": "object"}, dialect, type_id=api.type_id("target", "1.0")
    )
    instance = api.register_instance(target, {}, validate=True)
    api.request(
        "POST",
        "/entities",
        params={"validate": "true"},
        json={"id": instance + ".0", "type": target},
    )
    return {
        "T": target,
        "T*": target + "*",
        "D": derived,
        "T1.0": pinned,
        "I": instance,
        "I.0": instance + ".0",
    }


def _entity_ref_scope(spec, keyword, operands):
    """Builds a property schema from a spec such as ("K", "T") or ("not", "K", "D").

    "K" stands for the parametrized keyword; "union" accepts both kinds.
    """
    head, *rest = spec
    if head == "not":
        return {"not": _entity_ref_scope(tuple(rest), keyword, operands)}
    if head == "union":
        return {
            "type": "string",
            "anyOf": [
                {_TYPE_REF: operands[rest[0]]},
                {_INSTANCE_REF: operands[rest[0]]},
            ],
        }
    return {"type": "string", (keyword if head == "K" else head): operands[rest[0]]}


_ENTITY_REF_EVOLUTION = [
    pytest.param(("K", "T"), ("K", "T"), _COMPATIBLE, id="equal"),
    pytest.param(("K", "T"), ("K", "T*"), _COMPATIBLE, id="chain_wildcard_equal"),
    pytest.param(("K", "T"), ("K", "D"), _NARROWING, id="derived_root_narrows"),
    pytest.param(("K", "D"), ("K", "T"), _WIDENING, id="base_root_widens"),
    pytest.param(("K", "T"), ("K", "T1.0"), _NARROWING, id="pinned_minor_narrows"),
    pytest.param(("not", "K", "T"), ("not", "K", "D"), _WIDENING, id="negated_narrowing"),
]


@pytest.mark.parametrize("old_spec,new_spec,expected_verdicts", _ENTITY_REF_EVOLUTION)
@pytest.mark.parametrize("keyword", [_TYPE_REF, _INSTANCE_REF])
def test_entity_ref_evolution(
    gts_api, schema_dialect, keyword, old_spec, new_spec, expected_verdicts
):
    """Isolated constraints compare kind-filtered scopes (README §9.6.1)."""
    _check_entity_ref_evolution(
        gts_api, schema_dialect, keyword, old_spec, new_spec, expected_verdicts, False
    )


@pytest.mark.parametrize(
    "old_spec,new_spec,expected_verdicts,unknown_allowed",
    [
        pytest.param(
            (_TYPE_REF, "T"), (_INSTANCE_REF, "T"), _INCOMPATIBLE, False,
            id="type_to_instance",
        ),
        pytest.param(
            (_INSTANCE_REF, "T"), (_TYPE_REF, "T"), _INCOMPATIBLE, False,
            id="instance_to_type",
        ),
        pytest.param(
            (_INSTANCE_REF, "I"), (_INSTANCE_REF, "I.0"), _NARROWING, False,
            id="instance_operand_pinned_minor",
        ),
        pytest.param(
            (_INSTANCE_REF, "I"), (_INSTANCE_REF, "T"), _WIDENING, False,
            id="instance_operand_to_type_root",
        ),
        pytest.param(
            ("union", "T"), (_TYPE_REF, "T"), _NARROWING, True,
            id="union_to_type_only",
        ),
        pytest.param(
            (_INSTANCE_REF, "T"), ("union", "T"), _WIDENING, True,
            id="instance_only_to_union",
        ),
    ],
)
def test_entity_ref_kind_evolution(
    gts_api, schema_dialect, old_spec, new_spec, expected_verdicts, unknown_allowed
):
    """Switching between nonempty type and instance scopes satisfies neither
    inclusion; compositions may be reported `unknown`, never wrongly."""
    _check_entity_ref_evolution(
        gts_api, schema_dialect, None, old_spec, new_spec, expected_verdicts,
        unknown_allowed,
    )


def _check_entity_ref_evolution(
    api, dialect, keyword, old_spec, new_spec, expected_verdicts, unknown_allowed
):
    operands = _entity_ref_operands(api, dialect)
    types = []
    for name, version, spec in (("old", "1.0", old_spec), ("new", "1.1", new_spec)):
        types.append(
            api.register(
                name,
                {
                    "type": "object",
                    "required": ["ref"],
                    "properties": {"ref": _entity_ref_scope(spec, keyword, operands)},
                },
                dialect,
                type_id=api.type_id("evolution", version),
            )
        )
    _check_compatibility(api, *types, expected_verdicts, unknown_allowed)


@pytest.mark.parametrize(
    "old_operand,new_operand,expected_verdicts",
    [
        # The v1.0 and v1.1 roots select disjoint scopes.
        pytest.param("/$id", "/$id", _INCOMPATIBLE, id="both_self"),
        pytest.param("new_type_id", "/$id", _COMPATIBLE, id="new_self_equals_literal"),
        pytest.param("/$id", "old_type_id", _COMPATIBLE, id="old_self_equals_literal"),
    ],
)
@pytest.mark.parametrize("keyword", [_TYPE_REF, _INSTANCE_REF])
def test_entity_ref_evolution_resolves_each_self_reference(
    gts_api, schema_dialect, keyword, old_operand, new_operand, expected_verdicts
):
    """`/$id` names the schema it is resolved for, on each side."""
    api = gts_api
    type_ids = {
        "old_type_id": api.type_id("self", "1.0"),
        "new_type_id": api.type_id("self", "1.1"),
    }
    types = [
        api.register(
            name,
            {
                "type": "object",
                "required": ["ref"],
                "properties": {
                    "ref": {"type": "string", keyword: type_ids.get(operand, operand)},
                },
            },
            schema_dialect,
            type_id=type_ids[name + "_type_id"],
            # A literal operand may name the other version, registered later.
            mode="none",
        )
        for name, operand in (("old", old_operand), ("new", new_operand))
    ]
    _check_compatibility(api, *types, expected_verdicts)

if __name__ == "__main__":
    TestCaseTestOp8Compatibility_BackwardCompatible().test_start()
