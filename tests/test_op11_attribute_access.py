from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseTestOp11AttrAccess_ExistingFields(HttpRunner):
    """OP#11 - Attribute Access: Access nested field"""
    config = Config("OP#11 - Attribute Access (nested field)").base_url(
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
                "$$id": "gts://gts.x.test11.events.type.v1~",
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
                "$$id": (
                    "gts://gts.x.test11.events.type.v1~"
                    "x.test11.nested.event.v1.0~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test11.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.test11.events.type.v1~"
                                    "x.test11.nested.event.v1.0~"
                                )
                            },
                            "payload": {
                                "type": "object",
                                "required": ["orderId", "customer"],
                                "properties": {
                                    "orderId": {"type": "string"},
                                    "customer": {
                                        "type": "object",
                                        "required": ["name", "email"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
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
        # Register instance
        Step(
            RunRequest("register instance")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.test11.events.type.v1~"
                    "x.test11.nested.type.v1.0~"
                    "x.test11.my.event.v1.0"
                ),
                "type": (
                    "gts.x.test11.events.type.v1~"
                    "x.test11.nested.type.v1.0~"
                ),
                "eventId": "ad4g5h67-8901-72de-2345-def456789",
                "tenantId": "44444444-5555-6666-7777-888888888888",
                "occurredAt": "2025-09-20T21:00:00Z",
                "payload": {
                    "orderId": "order-12345",
                    "customer": {
                        "name": "John Doe",
                        "email": "john.doe@example.com"
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Access root field 'eventId'
        Step(
            RunRequest("access root field eventId")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.events.type.v1~"
                        "x.test11.nested.type.v1.0~"
                        "x.test11.my.event.v1.0@eventId"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", "ad4g5h67-8901-72de-2345-def456789")
        ),
        # Access nested field 'payload.customer.email'
        Step(
            RunRequest("access nested field")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.events.type.v1~"
                        "x.test11.nested.type.v1.0~"
                        "x.test11.my.event.v1.0@payload.customer.email"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", "john.doe@example.com")
        ),
    ]


class TestCaseTestOp11AttrAccess_NonExistentField(HttpRunner):
    """OP#11 - Attribute Access: Access non-existent field"""
    config = Config("OP#11 - Attribute Access (non-existent)").base_url(
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
                "$$id": "gts://gts.x.test11.events.type.v1~",
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
        # Register instance
        Step(
            RunRequest("register instance")
            .post("/entities")
            .with_json({
                "id": (
                    "gts.x.test11.events.type.v1~"
                    "x.test11.missing.event.v1.0"
                ),
                "type": (
                    "gts.x.test11.events.type.v1~"
                ),
                "eventId": "be5h6i78-9012-83ef-3456-efg567890",
                "tenantId": "55555555-6666-7777-8888-999999999999",
                "occurredAt": "2025-09-20T22:00:00Z",
                "payload": {
                    "field1": "value1"
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Access non-existent field
        Step(
            RunRequest("access non-existent field")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.events.type.v1~"
                        "x.test11.missing.event.v1.0@payload.nonExistent"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", False)
        ),
    ]


class TestCaseTestOp11AttrAccess_MissingAtSymbol(HttpRunner):
    """OP#11 - Attribute Access: Missing @ symbol in path should fail"""
    config = Config("OP#11 - Attribute Access (missing @)").base_url(
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
                "$$id": "gts://gts.x.test11.events.type.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "type", "tenantId", "occurredAt"],
                "properties": {
                    "type": {"type": "string"},
                    "eventId": {"type": "string", "format": "uuid"},
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
                "$$id": (
                    "gts://gts.x.test11.events.type.v1~"
                    "x.test11.nosymbol.event.v1.0~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test11.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.test11.events.type.v1~"
                                    "x.test11.nosymbol.event.v1.0~"
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
        # Register instance (anonymous instance with UUID id)
        Step(
            RunRequest("register instance")
            .post("/entities")
            .with_json({
                "id": "cf6i7j89-0123-94fg-4567-fgh678901234",
                "type": (
                    "gts.x.test11.events.type.v1~"
                    "x.test11.nosymbol.event.v1.0~"
                ),

                "tenantId": "66666666-7777-8888-9999-000000000000",
                "occurredAt": "2025-09-20T23:00:00Z",
                "payload": {
                    "field1": "value1"
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Access without @ symbol (should fail)
        Step(
            RunRequest("access without @ symbol")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.events.type.v1~"
                        "x.test11.nosymbol.event.v1.0"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", False)
        ),
    ]


class TestCaseTestOp11Attribute_ArrayElementAccess(HttpRunner):
    """Test accessing array elements by index"""
    config = Config("OP#11 Extended - Array Element Access").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema with array
        Step(
            RunRequest("register schema with array")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test11.array_access.order.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "orderId": {"type": "string"},
                    "items": {"type": "array"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register instance with array data
        Step(
            RunRequest("register instance with array")
            .post("/entities")
            .with_json({
                "type": "gts.x.test11.array_access.order.v1~",
                "id": (
                    "gts.x.test11.array_access.order.v1~"
                    "x.test11._.order_arr.v1"
                ),
                "orderId": "ORD-123",
                "items": [
                    {"sku": "SKU-001", "name": "Item 1", "price": 10.99},
                    {"sku": "SKU-002", "name": "Item 2", "price": 20.99},
                    {"sku": "SKU-003", "name": "Item 3", "price": 30.99}
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Access first array element
        Step(
            RunRequest("access first array element")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.array_access.order.v1~"
                        "x.test11._.order_arr.v1@items[0].sku"
                    ),
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", "SKU-001")
        ),
        # Access second array element
        Step(
            RunRequest("access second array element")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.array_access.order.v1~"
                        "x.test11._.order_arr.v1"
                        "@items[1].name"
                    ),
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", "Item 2")
        ),
    ]


class TestCaseTestOp11Attribute_DeepNesting(HttpRunner):
    """Test accessing deeply nested attributes (5+ levels)"""
    config = Config("OP#11 Extended - Deep Nesting Access").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema
        Step(
            RunRequest("register deeply nested schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test11.deep.nested.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "level1": {"type": "object"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register instance with deep nesting
        Step(
            RunRequest("register deeply nested instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test11.deep.nested.v1~",
                "id": "gts.x.test11.deep.nested.v1~x.test11._.deep1.v1",
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "level5": {
                                    "level6": {
                                        "deepValue": "found-it"
                                    }
                                }
                            }
                        }
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Access deeply nested value
        Step(
            RunRequest("access deeply nested value")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.deep.nested.v1~"
                        "x.test11._.deep1.v1"
                        "@level1.level2.level3.level4.level5.level6.deepValue"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", "found-it")
        ),
    ]


class TestCaseTestOp11Attribute_MixedArrayAndNesting(HttpRunner):
    """Test accessing nested objects within arrays"""
    config = Config("OP#11 Extended - Mixed Array+Nesting").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema
        Step(
            RunRequest("register mixed schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test11.mixed.complex.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "dataId": {"type": "string"},
                    "records": {"type": "array"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register instance with mixed structure
        Step(
            RunRequest("register mixed instance")
            .post("/entities")
            .with_json({
                "type": "gts.x.test11.mixed.complex.v1~",
                "id": "gts.x.test11.mixed.complex.v1~x.test11._.mixed1.v1",
                "dataId": "DATA-001",
                "records": [
                    {
                        "recordId": "REC-001",
                        "details": {
                            "metadata": {
                                "author": "John Doe",
                                "tags": ["important", "urgent"]
                            }
                        }
                    },
                    {
                        "recordId": "REC-002",
                        "details": {
                            "metadata": {
                                "author": "Jane Smith",
                                "tags": ["review", "pending"]
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Access nested field in array element
        Step(
            RunRequest("access nested field in array")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.mixed.complex.v1~x.test11._.mixed1.v1"
                        "@records[0].details.metadata.author"
                    ),
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", "John Doe")
        ),
        # Access array within nested object
        Step(
            RunRequest("access array in nested object")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.mixed.complex.v1~x.test11._.mixed1.v1"
                        "@records[1].details.metadata.tags[0]"
                    ),
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", "review")
        ),
    ]


class TestCaseTestOp11Attribute_BooleanAndNumericValues(HttpRunner):
    """Test accessing boolean and numeric attribute values"""
    config = Config("OP#11 Extended - Boolean+Numeric Access").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema
        Step(
            RunRequest("register schema with various types")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test11.types.config.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "configId": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "maxRetries": {"type": "integer"},
                    "timeout": {"type": "number"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register instance
        Step(
            RunRequest("register instance with various types")
            .post("/entities")
            .with_json({
                "type": "gts.x.test11.types.config.v1~",
                "id": "gts.x.test11.types.config.v1~x.test11._.config1.v1",
                "configId": "CFG-001",
                "enabled": True,
                "maxRetries": 5,
                "timeout": 30.5
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Access boolean value
        Step(
            RunRequest("access boolean value")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.types.config.v1~x.test11._.config1.v1"
                        "@enabled"
                    ),
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
        ),
        # Access integer value
        Step(
            RunRequest("access integer value")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.types.config.v1~x.test11._.config1.v1"
                        "@maxRetries"
                    ),
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", 5)
        ),
        # Access float value
        Step(
            RunRequest("access float value")
            .get("/attr")
            .with_params(
                **{
                    "gts_with_path": (
                        "gts.x.test11.types.config.v1~x.test11._.config1.v1"
                        "@timeout"
                    ),
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.resolved", True)
            .assert_equal("body.value", 30.5)
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp11AttrAccess_ExistingFields().test_start()
    TestCaseTestOp11AttrAccess_NonExistentField().test_start()
    TestCaseTestOp11AttrAccess_MissingAtSymbol().test_start()
