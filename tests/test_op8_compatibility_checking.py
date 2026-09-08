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


class TestCaseOp8_EnumTypeIntersection(HttpRunner):
    """OP#8: enum and type assertions must be compared as an intersection."""

    config = Config("OP#8 - enum/type intersection").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register mixed enum schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.enumtype.sample.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["code"],
                "properties": {"code": {"enum": ["x", 1]}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register narrowed enum schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.enumtype.sample.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["code"],
                "properties": {"code": {"enum": ["x", 1], "type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("check enum type narrowing compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_type_id": "gts.x.test8.enumtype.sample.v1.0~",
                    "new_type_id": "gts.x.test8.enumtype.sample.v1.1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.backward_compatibility", "incompatible")
            .assert_equal("body.forward_compatibility", "compatible")
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp8Compatibility_BackwardCompatible().test_start()
