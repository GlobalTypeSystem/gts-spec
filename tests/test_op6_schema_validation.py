from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseTestOp6ValidateInstance_ValidInstance(HttpRunner):
    """OP#6 - Schema Validation: Validate valid instance against its schema"""
    config = Config("OP#6 - Validate Instance (valid)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.events.type.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "type", "tenantId", "occurredAt"],
                "properties": {
                    "type": {"type": "string"},
                    "id": {"type": "string", "format": "uuid"},
                    "tenantId": {"type": "string", "format": "uuid"},
                    "occurredAt": {"type": "string", "format": "date-time"},
                    "payload": {"type": "object"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived event schema
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test6.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {"const": "gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~"},
                            "payload": {
                                "type": "object",
                                "required": ["orderId", "customerId", "totalAmount", "items"],
                                "properties": {
                                    "orderId": {"type": "string", "format": "uuid"},
                                    "customerId": {"type": "string", "format": "uuid"},
                                    "totalAmount": {"type": "number"},
                                    "items": {"type": "array", "items": {"type": "object"}}
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register valid instance
        Step(
            RunRequest("register valid instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~",
                "id": "gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~x.y._.some_event.v1.0",
                "tenantId": "11111111-2222-3333-4444-555555555555",
                "occurredAt": "2025-09-20T18:35:00Z",
                "payload": {
                    "orderId": "af0e3c1b-8f1e-4a27-9a9b-b7b9b70c1f01",
                    "customerId": "0f2e4a9b-1c3d-4e5f-8a9b-0c1d2e3f4a5b",
                    "totalAmount": 149.99,
                    "items": [
                        {"sku": "SKU-ABC-001", "name": "Wireless Mouse", "qty": 1, "price": 49.99}
                    ]
                }
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # Validate the instance
        Step(
            RunRequest("validate instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~x.y._.some_event.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.id", "gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~x.y._.some_event.v1.0")
        ),
    ]


class TestCaseTestOp6ValidateInstance_InvalidInstance(HttpRunner):
    """OP#6 - Schema Validation: Validate invalid instance (missing required field)"""
    config = Config("OP#6 - Validate Instance (invalid)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.events.type.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "type", "tenantId", "occurredAt"],
                "properties": {
                    "type": {"type": "string"},
                    "id": {"type": "string", "format": "uuid"},
                    "tenantId": {"type": "string", "format": "uuid"},
                    "occurredAt": {"type": "string", "format": "date-time"},
                    "payload": {"type": "object"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived event schema
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test6.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {"const": "gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~"},
                            "payload": {
                                "type": "object",
                                "required": ["requiredField"],
                                "properties": {
                                    "requiredField": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register invalid instance (missing requiredField in payload)
        Step(
            RunRequest("register invalid instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~",
                "id": "gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~x.y._.some_event2.v1.0",
                "tenantId": "11111111-2222-3333-4444-555555555555",
                "occurredAt": "2025-09-20T18:35:00Z",
                "payload": {
                    "someOtherField": "value"
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate the instance - should fail
        Step(
            RunRequest("validate instance should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~x.y._.some_event2.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.id", "gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~x.y._.some_event2.v1.0")
        ),
    ]


class TestCaseTestOp6SchemaValidation_InvalidSchemaIdPrefix(HttpRunner):
    """OP#6 - Reject JSON Schema identifier values that start with 'gts.'"""

    config = Config(
        "OP#6 - Schema Validation: reject plain gts prefix in id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with plain gts prefix should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts.x.test6.invalid_id.plain_prefix.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp6SchemaValidation_InvalidSchemaIdWildcard(HttpRunner):
    """OP#6 - Reject JSON Schema identifier with wildcard after gts://"""

    config = Config(
        "OP#6 - Schema Validation: reject wildcard gts:// id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with wildcard gts:// id should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.test6.events.*.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp6SchemaValidation_SchemaMissingId(HttpRunner):
    """OP#6 - Reject JSON Schema documents missing $id"""

    config = Config(
        "OP#6 - Schema Validation: reject schema without $$id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema without $id should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp6SchemaValidation_SchemaNonGtsId(HttpRunner):
    """OP#6 - Reject JSON Schema documents whose $id is not a GTS identifier"""

    config = Config(
        "OP#6 - Schema Validation: reject non-GTS $$id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with non-GTS $id should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "http://globaltypesystem.org/schemas/foo",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp6SchemaValidation_UnknownInstanceFormat(HttpRunner):
    """OP#6 - Reject instances missing recognizable GTS id/type fields"""

    config = Config(
        "OP#6 - Schema Validation: reject unrecognized instance layout"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register instance without GTS fields should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "event_id": "c5a29a31-86c7-4b4e-9fa6-8a5db2d1a1c4",
                "event_type": "gts.x.core.events.type.v1~a.b.c.d.v1"
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp6ValidateInstance_NotFound(HttpRunner):
    """OP#6 - Schema Validation: Validate non-existent instance"""
    config = Config("OP#6 - Validate Instance (not found)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("validate non-existent instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.nonexistent.pkg.ns.type.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]



class TestCaseTestOp6Validation_FormatValidation(HttpRunner):
    """Test format validation (email, uuid, date-time)"""
    config = Config("OP#6 Extended - Format Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema with format constraints
        Step(
            RunRequest("register schema with formats")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.formats.user.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["userId", "email", "createdAt"],
                "properties": {
                    "userId": {"type": "string", "format": "uuid"},
                    "email": {"type": "string", "format": "email"},
                    "createdAt": {"type": "string", "format": "date-time"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register valid instance with correct formats
        Step(
            RunRequest("register valid formatted instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6.formats.user.v1~",
                "id": "gts.x.test6.formats.user.v1~x.test6._.user_inst.v1",
                "userId": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "createdAt": "2025-01-15T10:30:00Z"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate the instance
        Step(
            RunRequest("validate formatted instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": (
                    "gts.x.test6.formats.user.v1~x.test6._.user_inst.v1"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp6Validation_NestedObjects(HttpRunner):
    """Test validation of nested object structures"""
    config = Config("OP#6 Extended - Nested Object Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema with nested objects
        Step(
            RunRequest("register nested schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.nested.order.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["orderId", "customer", "items"],
                "properties": {
                    "orderId": {"type": "string"},
                    "customer": {
                        "type": "object",
                        "required": ["customerId", "name", "address"],
                        "properties": {
                            "customerId": {"type": "string"},
                            "name": {"type": "string"},
                            "address": {
                                "type": "object",
                                "required": ["street", "city", "country"],
                                "properties": {
                                    "street": {"type": "string"},
                                    "city": {"type": "string"},
                                    "country": {"type": "string"},
                                    "postalCode": {"type": "string"}
                                }
                            }
                        }
                    },
                    "items": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["sku", "quantity", "price"],
                            "properties": {
                                "sku": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                                "price": {"type": "number", "minimum": 0}
                            }
                        }
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register valid nested instance
        Step(
            RunRequest("register valid nested instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6.nested.order.v1~",
                "id": "gts.x.test6.nested.order.v1~x.test6._.order1.v1",
                "orderId": "ORD-12345",
                "customer": {
                    "customerId": "CUST-001",
                    "name": "John Doe",
                    "address": {
                        "street": "123 Main St",
                        "city": "New York",
                        "country": "USA",
                        "postalCode": "10001"
                    }
                },
                "items": [
                    {"sku": "SKU-001", "quantity": 2, "price": 29.99},
                    {"sku": "SKU-002", "quantity": 1, "price": 49.99}
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate nested instance
        Step(
            RunRequest("validate nested instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": (
                    "gts.x.test6.nested.order.v1~x.test6._.order1.v1"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp6Validation_EnumConstraints(HttpRunner):
    """Test enum value validation"""
    config = Config("OP#6 Extended - Enum Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema with enum
        Step(
            RunRequest("register schema with enum")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.enum.status.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["statusId", "status"],
                "properties": {
                    "statusId": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "approved", "rejected", "completed"]
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"]
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register valid instance with enum values
        Step(
            RunRequest("register valid enum instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6.enum.status.v1~",
                "id": "gts.x.test6.enum.status.v1~x.test6._.status1.v1",
                "statusId": "STATUS-001",
                "status": "approved",
                "priority": "high"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate enum instance
        Step(
            RunRequest("validate enum instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": (
                    "gts.x.test6.enum.status.v1~x.test6._.status1.v1"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp6Validation_ArrayConstraints(HttpRunner):
    """Test array validation with minItems and maxItems"""
    config = Config("OP#6 Extended - Array Constraints").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema with array constraints
        Step(
            RunRequest("register schema with array constraints")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.array.tags.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["itemId", "tags"],
                "properties": {
                    "itemId": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 5,
                        "items": {"type": "string"}
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register valid instance with array
        Step(
            RunRequest("register valid array instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6.array.tags.v1~",
                "id": "gts.x.test6.array.tags.v1~x.test6._.item1.v1",
                "itemId": "ITEM-001",
                "tags": ["electronics", "sale", "featured"]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate array instance
        Step(
            RunRequest("validate array instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": (
                    "gts.x.test6.array.tags.v1~x.test6._.item1.v1"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp6ValidateInstance_ValidInstance().test_start()
