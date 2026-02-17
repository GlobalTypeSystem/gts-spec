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
    """OP#8.1 - Backward Compatibility: Adding optional field"""
    config = Config("OP#8 - Backward Compatible (add optional)").base_url(
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
                    "userId": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (adds optional field with default)
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
                    "userId": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "default": {}
                    }
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
                    "old_schema_id": "gts.x.test8.compat.event.v1.0~",
                    "new_schema_id": "gts.x.test8.compat.event.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", True)
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
                    "old_schema_id": "gts.x.test8.compat.breaking.v1.0~",
                    "new_schema_id": "gts.x.test8.compat.breaking.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", False)
        ),
    ]


class TestCaseTestOp8Compatibility_ForwardCompatible(HttpRunner):
    """OP#8.2 - Forward Compatibility: Open model allows new fields"""
    config = Config("OP#8 - Forward Compatible (open model)").base_url(
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
        # Register v1.1 schema (adds new field)
        Step(
            RunRequest("register v1.1 schema with new field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.forward.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "newField"],
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
                    "old_schema_id": "gts.x.test8.compat.forward.v1.0~",
                    "new_schema_id": "gts.x.test8.compat.forward.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_forward_compatible", True)
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
                    "old_schema_id": "gts.x.test8.compat.fwd_break.v1.0~",
                    "new_schema_id": "gts.x.test8.compat.fwd_break.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_forward_compatible", False)
        ),
    ]


class TestCaseTestOp8Compatibility_FullyCompatible(HttpRunner):
    """OP#8.3 - Full Compatibility: Both backward and forward compatible"""
    config = Config("OP#8 - Fully Compatible").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register v1.0 schema (open model)
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.full.v1.0~",
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
        # Register v1.1 schema (adds optional field with default)
        Step(
            RunRequest("register v1.1 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test8.compat.full.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId"],
                "properties": {
                    "eventId": {"type": "string"},
                    "optionalField": {
                        "type": "string",
                        "default": "default_value"
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
                    "old_schema_id": "gts.x.test8.compat.full.v1.0~",
                    "new_schema_id": "gts.x.test8.compat.full.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", True)
            .assert_equal("body.is_forward_compatible", True)
            .assert_equal("body.is_fully_compatible", True)
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
                    "old_schema_id": "gts.x.test8.compat.typechange.v1.0~",
                    "new_schema_id": "gts.x.test8.compat.typechange.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", False)
            .assert_equal("body.is_forward_compatible", False)
            .assert_equal("body.is_fully_compatible", False)
        ),
    ]


class TestCaseTestOp8Compatibility_EnumExpansion(HttpRunner):
    """OP#8 - Enum Expansion: Forward compatible, not backward"""
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
        # Check compatibility: forward compatible, not backward
        Step(
            RunRequest("check enum expansion compatibility")
            .get("/compatibility")
            .with_params(
                **{
                    "old_schema_id": "gts.x.test8.compat.enum.v1.0~",
                    "new_schema_id": "gts.x.test8.compat.enum.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", False)
            .assert_equal("body.is_forward_compatible", True)
            .assert_equal("body.is_fully_compatible", False)
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
                    "old_schema_id": (
                        "gts.x.test8.nested_compat.order.v1.0~"
                    ),
                    "new_schema_id": (
                        "gts.x.test8.nested_compat.order.v1.1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", True)
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
                    "old_schema_id": (
                        "gts.x.test8.constraints.product.v1.0~"
                    ),
                    "new_schema_id": (
                        "gts.x.test8.constraints.product.v1.1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", True)
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
                    "old_schema_id": "gts.x.test8.tight.item.v1.0~",
                    "new_schema_id": "gts.x.test8.tight.item.v1.1~"
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", False)
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
                    "old_schema_id": (
                        "gts.x.test8.array_compat.list.v1.0~"
                    ),
                    "new_schema_id": (
                        "gts.x.test8.array_compat.list.v1.1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.is_backward_compatible", True)
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp8Compatibility_BackwardCompatible().test_start()
