from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseTestOp9Cast_MinorVersionUpcast(HttpRunner):
    """OP#9 - Version Casting: Cast instance from v1.0 to v1.1"""
    config = Config("OP#9 - Cast (v1.0 to v1.1)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test9.events.type.v1~",
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
        # Register v1.0 schema
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test9.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.0~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test9.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.test9.events.type.v1~"
                                    "x.commerce.orders.order_placed.v1.0~"
                                )
                            },
                            "payload": {
                                "type": "object",
                                "required": [
                                    "orderId",
                                    "customerId",
                                    "totalAmount",
                                    "items"
                                ],
                                "properties": {
                                    "orderId": {
                                        "type": "string",
                                        "format": "uuid"
                                    },
                                    "customerId": {
                                        "type": "string",
                                        "format": "uuid"
                                    },
                                    "totalAmount": {"type": "number"},
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema (adds optional field)
        Step(
            RunRequest("register v1.1 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test9.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test9.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.test9.events.type.v1~"
                                    "x.commerce.orders.order_placed.v1.1~"
                                )
                            },
                            "payload": {
                                "type": "object",
                                "required": [
                                    "orderId",
                                    "customerId",
                                    "totalAmount",
                                    "items"
                                ],
                                "properties": {
                                    "orderId": {
                                        "type": "string",
                                        "format": "uuid"
                                    },
                                    "customerId": {
                                        "type": "string",
                                        "format": "uuid"
                                    },
                                    "totalAmount": {"type": "number"},
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    },
                                    "new_field_in_v1_1": {
                                        "type": "string",
                                        "default": "some_value"
                                    }
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.0 instance
        Step(
            RunRequest("register v1.0 instance")
            .post("/entities")
            .with_json({
                "type": (
                    "gts.x.test9.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.0~"
                ),
                "id": "gts.x.test9.events.type.v1~x.commerce.orders.order_placed.v1.0~x.y.some.instance.v1.0",
                "tenantId": "11111111-2222-3333-4444-555555555555",
                "occurredAt": "2025-09-20T18:35:00Z",
                "payload": {
                    "orderId": "af0e3c1b-8f1e-4a27-9a9b-b7b9b70c1f01",
                    "customerId": "0f2e4a9b-1c3d-4e5f-8a9b-0c1d2e3f4a5b",
                    "totalAmount": 149.99,
                    "items": [
                        {
                            "sku": "SKU-ABC-001",
                            "name": "Wireless Mouse",
                            "qty": 1,
                            "price": 49.99
                        }
                    ]
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Cast from v1.0 to v1.1
        Step(
            RunRequest("cast from v1.0 to v1.1")
            .post("/cast")
            .with_json({
                "instance_id": (
                    "gts.x.test9.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.0~"
                    "x.y.some.instance.v1.0"
                ),
                "to_type_id": (
                    "gts.x.test9.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.casted_entity.payload.new_field_in_v1_1", "some_value")
        ),
    ]


class TestCaseTestOp9Cast_MinorVersionDowncast(HttpRunner):
    """OP#9 - Version Casting: Cast instance from v1.1 to v1.0"""
    config = Config("OP#9 - Cast (v1.1 to v1.0)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test9.events.type.v1~",
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
        # Register v1.0 schema
        Step(
            RunRequest("register v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test9.events.type.v1~"
                    "x.test9.cast.event.v1.0~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test9.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.test9.events.type.v1~"
                                    "x.test9.cast.event.v1.0~"
                                )
                            },
                            "payload": {
                                "type": "object",
                                "required": ["field1"],
                                "properties": {
                                    "field1": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema
        Step(
            RunRequest("register v1.1 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test9.events.type.v1~"
                    "x.test9.cast.event.v1.1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test9.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.test9.events.type.v1~"
                                    "x.test9.cast.event.v1.1~"
                                )
                            },
                            "payload": {
                                "type": "object",
                                "required": ["field1"],
                                "properties": {
                                    "field1": {"type": "string"},
                                    "field2": {
                                        "type": "string",
                                        "default": "default_value"
                                    }
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 instance
        Step(
            RunRequest("register v1.1 instance")
            .post("/entities")
            .with_json({
                "type": (
                    "gts.x.test9.events.type.v1~"
                    "x.test9.cast.event.v1.1~"
                ),
                "id": "8b2e3f45-6789-50bc-0123-bcdef234567",
                "tenantId": "22222222-3333-4444-5555-666666666666",
                "occurredAt": "2025-09-20T19:00:00Z",
                "payload": {
                    "field1": "value1",
                    "field2": "value2"
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Cast from v1.1 to v1.0 (downcast, removes field2)
        Step(
            RunRequest("cast from v1.1 to v1.0")
            .post("/cast")
            .with_json({
                "instance_id": (
                    "gts.x.test9.events.type.v1~"
                    "x.test9.cast.event.v1.1~"
                ),
                "to_type_id": (
                    "gts.x.test9.events.type.v1~"
                    "x.test9.cast.event.v1.0~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp9Cast_IncompatibleMajorVersion(HttpRunner):
    """OP#9 - Version Casting: Fail on incompatible major version"""
    config = Config("OP#9 - Cast (incompatible major)").base_url(
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
                "$$id": "gts://gts.x.test9.version.type.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v2.0 schema (breaking change)
        Step(
            RunRequest("register v2.0 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test9.version.type.v2.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "newRequiredField"],
                "properties": {
                    "id": {"type": "string"},
                    "newRequiredField": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.0 instance
        Step(
            RunRequest("register v1.0 instance")
            .post("/entities")
            .with_json({
                "id": "test-id-123"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp9Cast_SchemaToSchemaNotAllowed(HttpRunner):
    """OP#9 - Version Casting: Fail when attempting to cast from schema to schema"""
    config = Config("OP#9 - Cast (schema to schema not allowed)").base_url(
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
                "$$id": "gts://gts.x.test9.schema2schema.type.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register v1.1 schema
        Step(
            RunRequest("register v1.1 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test9.schema2schema.type.v1.1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                    "newField": {
                        "type": "string",
                        "default": "default_value"
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Attempt cast from schema to schema (should fail)
        Step(
            RunRequest("cast from schema to schema should fail")
            .post("/cast")
            .with_json({
                "instance_id": "gts.x.test9.schema2schema.type.v1.0~",
                "to_type_id": "gts.x.test9.schema2schema.type.v1.1~"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_contains("body.error", "must be an instance")
        ),
    ]


def _enum_cast_steps(case_name, old_enum, new_enum, backward, forward):
    """Build a cast case with the enum constraint inside a property allOf."""
    old_constraint = {"type": "string"}
    new_constraint = {"type": "string"}
    if old_enum is not None:
        old_constraint["enum"] = old_enum
    if new_enum is not None:
        new_constraint["enum"] = new_enum
    old_status = {"allOf": [old_constraint]}
    new_status = {"allOf": [new_constraint]}

    old_type_id = f"gts.x.test9.enum_{case_name}.event.v1.0~"
    new_type_id = f"gts.x.test9.enum_{case_name}.event.v1.1~"
    instance_id = f"{old_type_id}x.test9._.instance.v1"

    return [
        Step(
            RunRequest(f"register {case_name} v1.0 schema")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{old_type_id}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["status"],
                "properties": {"status": old_status},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest(f"register {case_name} v1.1 schema")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{new_type_id}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["status"],
                "properties": {"status": new_status},
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest(f"register {case_name} v1.0 instance")
            .post("/entities")
            .with_json({
                "id": instance_id,
                "type": old_type_id,
                "status": "active",
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest(f"cast {case_name} instance")
            .post("/cast")
            .with_json({"instance_id": instance_id, "to_type_id": new_type_id})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.casted_entity.status", "active")
            .assert_equal("body.is_backward_compatible", backward)
            .assert_equal("body.is_forward_compatible", forward)
            .assert_equal("body.is_fully_compatible", backward and forward)
        ),
    ]


class TestCaseTestOp9Cast_EnumRemoved(HttpRunner):
    """OP#9 - Removing an enum widens the target accepted-instance set.

    Every source instance remains valid under the target schema, so the cast
    result is backward-compatible but not forward-compatible.
    """
    config = Config("OP#9 - Cast (enum removed)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _enum_cast_steps(
        "removed", ["active", "inactive"], None, True, False
    )


class TestCaseTestOp9Cast_EnumAdded(HttpRunner):
    """OP#9 - Adding an enum narrows the target accepted-instance set.

    The selected instance remains castable, but the schema verdict is
    forward-compatible only because the target rejects previously valid values.
    """
    config = Config("OP#9 - Cast (enum added)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _enum_cast_steps(
        "added", None, ["active", "inactive"], False, True
    )


if __name__ == "__main__":
    TestCaseTestOp9Cast_MinorVersionUpcast().test_start()
