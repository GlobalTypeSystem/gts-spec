"""OP#6 - Schema Validation tests.

Validates object instances against their corresponding JSON Schemas,
including well-known instances (chained GTS IDs), anonymous instances
(UUID id + separate type field), schema registration rules, and
extended JSON Schema constraints (formats, nesting, enums, arrays).
"""

from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _base_event_schema(type_id, id_property=None):
    """Build a base event envelope schema with the given GTS Type Identifier."""
    if id_property is None:
        id_property = {"type": "string"}
    return {
        "$$id": f"gts://{type_id}",
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["id", "type", "tenantId", "occurredAt"],
        "properties": {
            "type": {"type": "string"},
            "id": id_property,
            "tenantId": {"type": "string", "format": "uuid"},
            "occurredAt": {"type": "string", "format": "date-time"},
            "payload": {"type": "object"}
        },
        "additionalProperties": False
    }


def _derived_event_schema(base_id, derived_id, payload_schema):
    """Build a derived event schema that extends a base via allOf with a specific payload."""
    return {
        "$$id": f"gts://{derived_id}",
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "allOf": [
            {"$$ref": f"gts://{base_id}"},
            {
                "type": "object",
                "required": ["type", "payload"],
                "properties": {
                    "type": {"const": derived_id},
                    "payload": payload_schema
                }
            }
        ]
    }


ORDER_PLACED_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": ["orderId", "customerId", "totalAmount", "items"],
    "properties": {
        "orderId": {"type": "string", "format": "uuid"},
        "customerId": {"type": "string", "format": "uuid"},
        "totalAmount": {"type": "number"},
        "items": {"type": "array", "items": {"type": "object"}}
    }
}

REQUIRED_FIELD_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": ["requiredField"],
    "properties": {
        "requiredField": {"type": "string"}
    }
}


# ---------------------------------------------------------------------------
# Instance validation tests (well-known instances)
# ---------------------------------------------------------------------------


class TestCaseTestOp6ValidateInstance_ValidInstance(HttpRunner):
    """OP#6 - Validate a well-known instance against its derived schema.

    Registers base and derived event schemas, then a valid instance with a
    chained GTS ID. Validation must pass.
    """
    config = Config("OP#6 - Validate Instance (valid)").base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json(_base_event_schema("gts.x.test6.events.type.v1~"))
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived event schema
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json(_derived_event_schema(
                "gts.x.test6.events.type.v1~",
                "gts.x.test6.events.type.v1~x.commerce.orders.order_placed.v1.0~",
                ORDER_PLACED_PAYLOAD_SCHEMA,
            ))
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
                "tenantId": "11111111-2222-3333-8444-555555555555",
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
    """OP#6 - Validate a well-known instance that violates its schema.

    The instance is missing a required payload field.
    Validation must fail.
    """
    config = Config("OP#6 - Validate Instance (invalid)").base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json(_base_event_schema("gts.x.test6.events.type.v1~"))
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived event schema
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json(_derived_event_schema(
                "gts.x.test6.events.type.v1~",
                "gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~",
                REQUIRED_FIELD_PAYLOAD_SCHEMA,
            ))
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register invalid instance (missing requiredField in payload)
        Step(
            RunRequest("register invalid instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~",
                "id": "gts.x.test6.events.type.v1~x.test6.invalid.event.v1.0~x.y._.some_event2.v1.0",
                "tenantId": "11111111-2222-3333-8444-555555555555",
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


# ---------------------------------------------------------------------------
# Schema registration rejection tests
# ---------------------------------------------------------------------------


class TestCaseTestOp6SchemaValidation_InvalidSchemaIdPrefix(HttpRunner):
    """OP#6 - Reject schema whose $id uses a raw ``gts.`` prefix.

    A schema's ``$id`` must use the ``gts://`` URI scheme to express a
    GTS Type Identifier in URI-compatible form. Registration must return 422.
    """

    config = Config(
        "OP#6 - Schema Validation: reject plain gts prefix in id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Reject schema whose $id contains a wildcard segment.

    Wildcards are not permitted in GTS Type Identifiers.
    Registration must return 422.
    """

    config = Config(
        "OP#6 - Schema Validation: reject wildcard gts:// id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Reject schema document that is missing a $id field.

    Every GTS schema must declare its identifier via $id.
    Registration must return 422.
    """

    config = Config(
        "OP#6 - Schema Validation: reject schema without $$id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Reject schema whose $id is not a GTS identifier.

    Only ``gts://`` URIs are valid ``$id`` forms for GTS Type Identifiers.
    Registration must return 422.
    """

    config = Config(
        "OP#6 - Schema Validation: reject non-GTS $$id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Reject instance with no recognizable GTS id/type fields.

    Instances must contain standard GTS fields (id, type, gtsId, etc.).
    Registration must return 422.
    """

    config = Config(
        "OP#6 - Schema Validation: reject unrecognized instance layout"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Validate an instance that does not exist in the store.

    Validation must return ok=false.
    """
    config = Config("OP#6 - Validate Instance (not found)").base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
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


# ---------------------------------------------------------------------------
# Extended JSON Schema constraint tests
# ---------------------------------------------------------------------------


class TestCaseTestOp6Validation_FormatValidation(HttpRunner):
    """OP#6 - Validate JSON Schema format keywords (email, uuid, date-time).

    Registers a schema with format constraints and a conforming instance.
    Validation must pass.
    """
    config = Config("OP#6 Extended - Format Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Validate deeply nested object structures.

    Schema defines nested customer/address and items array.
    Validation of a conforming instance must pass.
    """
    config = Config("OP#6 Extended - Nested Object Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Validate enum value constraints.

    Schema restricts status and priority to fixed sets.
    Validation of a conforming instance must pass.
    """
    config = Config("OP#6 Extended - Enum Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        """Run the test steps."""
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
    """OP#6 - Validate array constraints (minItems / maxItems).

    Schema requires 1-5 string tags.
    Validation of a conforming instance must pass.
    """
    config = Config("OP#6 Extended - Array Constraints").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        """Run the test steps."""
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


# ---------------------------------------------------------------------------
# Anonymous instance validation tests (UUID id + separate type field)
# ---------------------------------------------------------------------------


class TestCaseTestOp6ValidateInstance_AnonymousInstance(HttpRunner):
    """OP#6 - Validate an anonymous instance identified by UUID.

    The instance uses a plain UUID in the ``id`` field and a separate
    ``type`` field for schema resolution (spec section 3.7).
    Validation must pass.
    """
    config = Config("OP#6 - Validate Anonymous Instance (valid)").base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json(_base_event_schema(
                "gts.x.test6anon.events.type.v1~",
                id_property={"type": "string", "format": "uuid"},
            ))
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived event schema
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json(_derived_event_schema(
                "gts.x.test6anon.events.type.v1~",
                "gts.x.test6anon.events.type.v1~x.commerce.orders.order_placed.v1.0~",
                ORDER_PLACED_PAYLOAD_SCHEMA,
            ))
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register anonymous instance with UUID id and separate type field
        Step(
            RunRequest("register anonymous instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6anon.events.type.v1~x.commerce.orders.order_placed.v1.0~",
                "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
                "tenantId": "11111111-2222-3333-8444-555555555555",
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
        # Validate the anonymous instance using its UUID
        Step(
            RunRequest("validate anonymous instance")
            .post("/validate-instance")
            .with_json({
                "instance_id": "7a1d2f34-5678-49ab-9012-abcdef123456"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.id", "7a1d2f34-5678-49ab-9012-abcdef123456")
        ),
    ]


class TestCaseTestOp6ValidateInstance_AnonymousInstance_Invalid(HttpRunner):
    """OP#6 - Validate an anonymous instance that violates its schema.

    The instance uses a plain UUID in the ``id`` field and a separate
    ``type`` field, but its payload is missing a required field.
    Validation must fail.
    """
    config = Config("OP#6 - Validate Anonymous Instance (invalid)").base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json(_base_event_schema(
                "gts.x.test6anon.events.type.v1~",
                id_property={"type": "string", "format": "uuid"},
            ))
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived event schema with required payload fields
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json(_derived_event_schema(
                "gts.x.test6anon.events.type.v1~",
                "gts.x.test6anon.events.type.v1~x.test6anon.invalid.event.v1.0~",
                REQUIRED_FIELD_PAYLOAD_SCHEMA,
            ))
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register invalid anonymous instance (missing requiredField in payload)
        Step(
            RunRequest("register invalid anonymous instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test6anon.events.type.v1~x.test6anon.invalid.event.v1.0~",
                "id": "8b2e3f45-6789-4abc-8123-bcdef1234567",
                "tenantId": "11111111-2222-3333-8444-555555555555",
                "occurredAt": "2025-09-20T18:35:00Z",
                "payload": {
                    "someOtherField": "value"
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate the anonymous instance - should fail
        Step(
            RunRequest("validate anonymous instance should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "8b2e3f45-6789-4abc-8123-bcdef1234567"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.id", "8b2e3f45-6789-4abc-8123-bcdef1234567")
        ),
    ]


# ---------------------------------------------------------------------------
# x-gts-abstract tests (OP#6 extension — abstract types cannot have direct instances)
# ---------------------------------------------------------------------------


class TestCaseOp6_AbstractType_RejectWellKnownInstance(HttpRunner):
    """OP#6 / x-gts-abstract: Well-known instance of abstract type MUST fail validation.

    Base type declares x-gts-abstract: true. Registering and validating a
    well-known instance whose rightmost type is the abstract type MUST fail.
    """

    config = Config("OP#6 x-gts-abstract: reject well-known instance of abstract type").base_url(
        get_gts_base_url()
    )
    teststeps = [
        # Register abstract base schema
        Step(
            RunRequest("register abstract base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.abstract.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "x-gts-abstract": True,
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
        # Register well-known instance of abstract type
        Step(
            RunRequest("register instance of abstract type")
            .post("/entities")
            .with_json({
                "id": "gts.x.test6.abstract.base.v1~x.test6._.my_item.v1",
                "name": "My Item",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate instance — should fail because base is abstract
        Step(
            RunRequest("validate instance of abstract type should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.test6.abstract.base.v1~x.test6._.my_item.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.id", "gts.x.test6.abstract.base.v1~x.test6._.my_item.v1")
        ),
    ]


class TestCaseOp6_AbstractType_RejectAnonInstance(HttpRunner):
    """OP#6 / x-gts-abstract: Anonymous instance of abstract type MUST fail validation.

    Combined anonymous instance whose type prefix is abstract MUST be rejected.
    """

    config = Config("OP#6 x-gts-abstract: reject anonymous instance of abstract type").base_url(
        get_gts_base_url()
    )
    teststeps = [
        # Register abstract base schema
        Step(
            RunRequest("register abstract base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.abstractanon.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "x-gts-abstract": True,
                "type": "object",
                "required": ["id", "type", "name"],
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "type": {"type": "string"},
                    "name": {"type": "string"},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register anonymous instance with type pointing to abstract schema
        Step(
            RunRequest("register anonymous instance of abstract type")
            .post("/entities")
            .with_json({
                "id": "a1b2c3d4-5678-4abc-8def-111111111111",
                "type": "gts.x.test6.abstractanon.base.v1~",
                "name": "Anon Item",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate instance — should fail because type is abstract
        Step(
            RunRequest("validate anonymous instance of abstract type should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "a1b2c3d4-5678-4abc-8def-111111111111",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.id", "a1b2c3d4-5678-4abc-8def-111111111111")
        ),
    ]


class TestCaseOp6_AbstractType_AllowInstanceOfConcreteDerived(HttpRunner):
    """OP#6 / x-gts-abstract: Instance of concrete derived type MUST pass.

    Abstract base A~, concrete derived A~B~. Instance of B~ should pass
    because B~ is not abstract.
    """

    config = Config("OP#6 x-gts-abstract: allow instance of concrete derived type").base_url(
        get_gts_base_url()
    )
    teststeps = [
        # Register abstract base schema
        Step(
            RunRequest("register abstract base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.abstractder.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "x-gts-abstract": True,
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
        # Register concrete derived schema
        Step(
            RunRequest("register concrete derived schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.abstractder.base.v1~x.test6._.concrete.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test6.abstractder.base.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "extra": {"type": "string"},
                        },
                    },
                ],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register well-known instance of concrete derived type
        Step(
            RunRequest("register instance of concrete derived type")
            .post("/entities")
            .with_json({
                "id": "gts.x.test6.abstractder.base.v1~x.test6._.concrete.v1~x.test6._.my_item.v1",
                "name": "My Item",
                "extra": "some value",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate instance — should pass because concrete.v1~ is not abstract
        Step(
            RunRequest("validate instance of concrete derived should pass")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.test6.abstractder.base.v1~x.test6._.concrete.v1~x.test6._.my_item.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseOp6_AbstractType_ValidateEntityRejectsInstance(HttpRunner):
    """OP#6 / x-gts-abstract: /validate-entity MUST also reject instance of abstract type.

    The unified /validate-entity endpoint must enforce the abstract constraint
    the same way /validate-instance does.
    """

    config = Config("OP#6 x-gts-abstract: validate-entity rejects instance of abstract type").base_url(
        get_gts_base_url()
    )
    teststeps = [
        # Register abstract base schema
        Step(
            RunRequest("register abstract base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.abstractent.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "x-gts-abstract": True,
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
        # Register well-known instance of abstract type
        Step(
            RunRequest("register instance of abstract type")
            .post("/entities")
            .with_json({
                "id": "gts.x.test6.abstractent.base.v1~x.test6._.my_item.v1",
                "name": "My Item",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate via /validate-entity — should fail because base is abstract
        Step(
            RunRequest("validate-entity instance of abstract type should fail")
            .post("/validate-entity")
            .with_json({
                "entity_id": "gts.x.test6.abstractent.base.v1~x.test6._.my_item.v1",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.entity_type", "instance")
        ),
    ]


class TestCaseOp6_AbstractType_RejectCombinedAnonInstance(HttpRunner):
    """OP#6 / x-gts-abstract: Combined anonymous instance (gts.type~UUID) of abstract type MUST fail.

    Tests the combined anonymous format where the type is resolved from the
    ID prefix (section 9.11.3.5).
    """

    config = Config("OP#6 x-gts-abstract: reject combined anonymous instance of abstract type").base_url(
        get_gts_base_url()
    )
    teststeps = [
        # Register abstract base schema
        Step(
            RunRequest("register abstract base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test6.abstractcomb.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "x-gts-abstract": True,
                "type": "object",
                "required": ["id", "type", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "name": {"type": "string"},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register combined anonymous instance (type prefix is abstract)
        Step(
            RunRequest("register combined anonymous instance of abstract type")
            .post("/entities")
            .with_json({
                "id": "gts.x.test6.abstractcomb.base.v1~d2e3f4a5-6789-4abc-8def-222222222222",
                "type": "gts.x.test6.abstractcomb.base.v1~",
                "name": "Combined Anon Item",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Validate combined anonymous instance — should fail because type is abstract
        Step(
            RunRequest("validate combined anonymous instance of abstract type should fail")
            .post("/validate-instance")
            .with_json({
                "instance_id": "gts.x.test6.abstractcomb.base.v1~d2e3f4a5-6789-4abc-8def-222222222222",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.id", "gts.x.test6.abstractcomb.base.v1~d2e3f4a5-6789-4abc-8def-222222222222")
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp6ValidateInstance_ValidInstance().test_start()
