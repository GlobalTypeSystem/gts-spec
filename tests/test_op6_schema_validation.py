"""OP#6 - Schema Validation tests.

Validates object instances against their corresponding JSON Schemas,
including well-known instances (chained GTS IDs), anonymous instances
(UUID id + separate type field), schema registration rules, and
extended JSON Schema constraints (formats, nesting, enums, arrays).
"""

from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    register as _register,
    register_instance as _register_instance,
    validate_instance as _validate_instance,
)
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
            .assert_equal("body.ok", False)
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
            .assert_equal("body.ok", False)
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
            .assert_equal("body.ok", False)
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
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp6SchemaValidation_SchemaGtsUriWithInvalidBody(HttpRunner):
    """OP#6 - Reject schema whose $id uses gts:// URI but has invalid body.

    A schema's ``$id`` must use the ``gts://`` URI scheme followed by a valid
    GTS Type Identifier starting with ``gts.``.  A value like
    ``gts://gtx.vendor.pkg.ns.type.v1~`` uses the correct URI scheme but has
    a malformed body (``gtx.`` instead of ``gts.``).  Registration must return
    422.
    """

    config = Config(
        "OP#6 - Schema Validation: reject gts:// with invalid body"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        Step(
            RunRequest(
                "register schema with gts:// URI but non-gts body should fail"
            )
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gtx.x.test6.invalid_uri_body.bad_prefix.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"]
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp6SchemaValidation_LiteralDoubleDollarIdRejected(HttpRunner):
    """OP#6 - Reject a schema that uses a literal ``$$id`` field.

    ``$$id``/``$$ref``/``$$schema`` are NOT GTS or JSON-Schema fields — the
    doubled ``$`` is purely an HttpRunner escaping artifact (HttpRunner
    unescapes ``$$`` -> ``$`` on the wire). A real, non-HttpRunner client that
    literally transmits ``$$id`` therefore provides no valid ``$id`` field, so
    schema registration must fail with 422.

    ESCAPING NOTE: because HttpRunner collapses ``$$`` -> ``$``, transmitting a
    literal two-dollar ``$$id`` requires writing ``$$$$id`` here. ``$$schema``
    transmits the real ``$schema`` keyword so the document is still recognized
    as a JSON Schema (isolating the bad ``$$id`` as the sole reason for
    rejection).
    """

    config = Config(
        "OP#6 - Schema Validation: reject literal double-dollar id"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with literal double-dollar id should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$$$id": "gts://gts.x.test6.literal_double_dollar.reject.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"]
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", True)
            .assert_contains("body.error", "Unable to detect GTS ID in schema")
        ),
    ]


class TestCaseTestOp6SchemaValidation_DoubleDollarSchemaAndId_TreatedAsInstance(HttpRunner):
    """OP#6 - Literal $$schema + literal $$id are treated as instance fields.

    Only canonical $schema marks a JSON Schema document. A literal $$schema is
    not a schema marker, and literal $$id is not the canonical id field.
    Therefore this payload is treated as an instance and (without a real id
    field) is rejected as an instance — the same as any JSON object lacking
    a recognizable GTS id field.

    ESCAPING: HttpRunner turns $$ -> $, so to transmit literal $$schema/$$id
    we send $$$$schema/$$$$id in the source below.
    """

    config = Config(
        "OP#6 - Schema Validation: literal double-dollar schema + id treated as instance"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register literal $$schema + $$id should be instance error")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$$$schema": "http://json-schema.org/draft-07/schema#",
                "$$$$id": "gts://gts.x.test6.double_dollar.instance_like.v1~",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", False)
            .assert_contains("body.error", "Unable to detect GTS ID in instance entity")
        ),
    ]


class TestCaseTestOp6SchemaValidation_DoubleDollarSchemaWithRealId_TreatedAsInstance(HttpRunner):
    """OP#6 - Literal $$schema + real $id is treated as an instance.

    Since $$schema is not a schema marker, the payload is not a type-schema.
    The real $id acts as an instance id field and registration succeeds as an
    instance entity.

    ESCAPING: $$$$schema transmits literal $$schema, while $$id transmits real
    $id.
    """

    config = Config(
        "OP#6 - Schema Validation: literal double-dollar schema with real id is instance"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register literal $$schema + real $id should be instance success")
            .post("/entities")
            .with_json({
                "$$$$schema": "http://json-schema.org/draft-07/schema#",
                "$$id": "gts://gts.x.test6.double_dollar.instance_ok.v1~",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.is_type_schema", False)
        ),
    ]


class TestCaseTestOp6SchemaValidation_DoubleDollarRefNotMapped(HttpRunner):
    """OP#6 - A literal ``$$ref`` must NOT be treated as JSON Schema ``$ref``.

    ``$$ref`` is an HttpRunner escaping artifact (HttpRunner unescapes ``$$`` ->
    ``$`` on the wire), not a JSON Schema keyword. A schema that references its
    parent via a literal ``$$ref`` therefore does NOT inherit the parent's
    constraints — the doubled keyword is an unknown no-op keyword.

    This is proven by contrast against a real ``$ref`` using the SAME base and
    the SAME (parent-violating) instance shape:

      - real ``$ref``  -> parent constraint inherited  -> instance FAILS (ok=False)
      - literal ``$$ref`` -> parent constraint ignored -> instance PASSES (ok=True)

    If a future regression re-introduced ``$$ref`` -> ``$ref`` mapping, the
    ``$$ref`` step below would flip to ok=False and this test would fail.

    ESCAPING NOTE: HttpRunner collapses ``$$`` -> ``$``, so ``$$id``/``$$schema``
    transmit the real ``$id``/``$schema`` keywords, ``$$ref`` transmits a real
    ``$ref``, and ``$$$$ref`` transmits a literal ``$$ref``.
    """

    config = Config(
        "OP#6 - Schema Validation: literal double-dollar ref is not a ref"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    _BASE = "gts.x.test6.dref.base.v1~"
    _DER_REF = "gts.x.test6.dref.base.v1~x.test6._.der_ref.v1~"
    _DER_DD = "gts.x.test6.dref.base.v1~x.test6._.der_dd.v1~"
    _INST_REF = "gts.x.test6.dref.base.v1~x.test6._.der_ref.v1~x.y._.i1.v1.0"
    _INST_DD = "gts.x.test6.dref.base.v1~x.test6._.der_dd.v1~x.y._.i2.v1.0"

    teststeps = [
        # Base type requires base_field.
        Step(
            RunRequest("register base schema requiring base_field")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{_BASE}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "type", "base_field"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "base_field": {"type": "string"},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        # --- Control: real $ref inherits the base constraint ---
        Step(
            RunRequest("register derived schema using real ref")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{_DER_REF}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": f"gts://{_BASE}"}],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register instance missing base_field, must be ok because no validation requested")
            .post("/entities")
            .with_json({"id": _INST_REF, "type": _DER_REF})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", _INST_REF)
            .assert_equal("body.type_id", _DER_REF)
        ),
        Step(
            RunRequest("validate instance under real ref should fail")
            .post("/validate-instance")
            .with_json({"instance_id": _INST_REF})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("register invalid ref instance with validation should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({"id": _INST_REF, "type": _DER_REF})
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "base_field")
        ),
        # --- Subject: literal $$ref does NOT inherit the base constraint ---
        Step(
            RunRequest("register derived schema using literal double-dollar ref")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{_DER_DD}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$$$ref": f"gts://{_BASE}"}],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register instance missing base_field (double-dollar variant)")
            .post("/entities")
            .with_json({"id": _INST_DD, "type": _DER_DD})
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate instance under literal double-dollar ref should pass")
            .post("/validate-instance")
            .with_json({"instance_id": _INST_DD})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest(
                "register literal double-dollar ref instance with validation should pass"
            )
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({"id": _INST_DD, "type": _DER_DD})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp6SchemaValidation_DoubleDollarRefDerivedSchemaMismatch(HttpRunner):
    """OP#6 - A derived-looking ID with literal ``$$ref`` is schema-incompatible.

    The GTS ID chain says that the second schema derives from the first, so
    schema validation must compare the two declarations. A literal ``$$ref``
    is not JSON Schema ``$ref`` and does not inherit the base declaration.
    Registering the derived schema with validation enabled must therefore
    reject the schema as incompatible with its GTS base.

    HttpRunner escaping: ``$$$$ref`` sends a literal ``$$ref`` on the wire.
    """

    config = Config(
        "OP#6 - Schema Validation: double-dollar ref derived mismatch"
    ).base_url(get_gts_base_url())

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    _BASE = "gts.x.test6.dref_mismatch.base.v1~"
    _DERIVED = "gts.x.test6.dref_mismatch.base.v1~x.test6._.literal_dd.v1~"

    teststeps = [
        Step(
            RunRequest("register base schema for derived mismatch")
            .post("/entities")
            .with_json({
                "$$id": f"gts://{_BASE}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["base_field"],
                "properties": {"base_field": {"type": "string"}},
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("reject derived schema with literal double-dollar ref")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": f"gts://{_DERIVED}",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$$$ref": f"gts://{_BASE}"}],
            })
            .validate()
            .assert_equal("status_code", 422)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", True)
            .assert_contains("body.error", "not compatible with base")
            .assert_contains("body.error", "base_field")
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


_STANDARD_FORMAT_TYPE_ID = "gts.x.test6.formats.standard.v1~"
_STANDARD_FORMATS = (
    ("uuidValue", "uuid", "550e8400-e29b-41d4-a716-446655440000", "not-a-uuid"),
    ("emailValue", "email", "user@example.com", "not-an-email"),
    ("dateTimeValue", "date-time", "2008-10-12T10:30:00Z", "2008-10-12 10:30:00Z"),
    ("dateTimeValueT", "date-time", "2011-07-22T10:30:00Z", "2011-07-22T10:30:00"),
    ("dateTimeFracValue", "date-time", "2025-06-19T10:30:00.123Z", "2025-06-19T10:30:61.123Z"),
    ("dateTimeTZValue", "date-time", "2027-04-26T10:30:00+01:00", "2027-04-26T10:30:00+25:00"),
    ("dateValue", "date", "2025-01-15", "2025-13-40"),
    ("timeValueOffset", "time", "10:30:00Z", "10:30:00"), # time offset is mandatory in 'time-format' draft-07
    ("timeValueOverflow", "time", "10:30:00Z", "10:00:61Z"),
    ("timeValueFracZ", "time", "10:30:00.123Z", "10:00:61.123Z"),
    ("timeValueTZ", "time", "10:30:00+01:00", "10:30:00+25:00"),
    ("uriValue", "uri", "https://example.com/resource", "://not-a-uri"),
    ("hostnameValue", "hostname", "example.com", "not a hostname"),
    ("ipv4Value", "ipv4", "192.168.1.1", "999.999.999.999"),
    ("ipv6Value", "ipv6", "2001:db8::1", "not-an-ipv6-address"),
    ("regexValue", "regex", "^[A-Za-z0-9]+$", "[unclosed"),
)
_STANDARD_FORMAT_VALUES = {
    field: valid for field, _, valid, _ in _STANDARD_FORMATS
}
_STANDARD_FORMAT_SCHEMA = {
    "type": "object",
    "required": [field for field, _, _, _ in _STANDARD_FORMATS],
    "properties": {
        field: {"type": "string", "format": format_name}
        for field, format_name, _, _ in _STANDARD_FORMATS
    },
}


class TestCaseTestOp6Validation_StandardFormats(HttpRunner):
    """OP#6 - Enforce standard JSON Schema formats on instance properties.

    ``url`` is not a standard JSON Schema format; HTTPS URL values are covered
    by the standard ``uri`` format instead.
    """
    config = Config("OP#6 Extended - Standard Format Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            f"gts://{_STANDARD_FORMAT_TYPE_ID}",
            _STANDARD_FORMAT_SCHEMA,
            "register schema with standard formats",
        ),
        _register_instance(
            {
                "type": _STANDARD_FORMAT_TYPE_ID,
                "id": f"{_STANDARD_FORMAT_TYPE_ID}x.test6._.valid_formats.v1.0",
                **_STANDARD_FORMAT_VALUES,
            },
            "register instance with valid standard formats",
        ),
        _validate_instance(
            f"{_STANDARD_FORMAT_TYPE_ID}x.test6._.valid_formats.v1.0",
            True,
            "validate instance with valid standard formats",
        ),
        *[
            _register_instance(
                {
                    "type": _STANDARD_FORMAT_TYPE_ID,
                    "id": (
                        f"{_STANDARD_FORMAT_TYPE_ID}"
                        f"x.test6._.invalid_{field.lower()}.v1.0"
                    ),
                    **{**_STANDARD_FORMAT_VALUES, field: invalid},
                },
                f"register instance with invalid {format_name}",
            )
            for field, format_name, _, invalid in _STANDARD_FORMATS
        ],
        *[
            _validate_instance(
                (
                    f"{_STANDARD_FORMAT_TYPE_ID}"
                    f"x.test6._.invalid_{field.lower()}.v1.0"
                ),
                False,
                f"reject instance with invalid {format_name}",
            )
            for field, format_name, _, _ in _STANDARD_FORMATS
        ],
    ]


_REGEX_ECMA262_TYPE_ID = "gts.x.test6.formats.regexecma.v1~"
_REGEX_ECMA262_SCHEMA = {
    "type": "object",
    "required": ["regexValue"],
    "properties": {"regexValue": {"type": "string", "format": "regex"}},
}

# Strings that ARE valid ECMA 262 regular expressions. The Draft-07 `regex`
# format asserts that the value is a regular expression valid according to the
# ECMA 262 dialect (README §9.2, ADR-0005), so these MUST validate.
_REGEX_ECMA262_VALID = (
    ("anchored_class", "^[A-Za-z0-9]+$"),
    ("shorthand_bounded", "\\d{3}-\\d{4}"),
    ("group_alternation", "(foo|bar)+"),
    ("range_bounded", "[a-z]{1,3}"),
    ("optional_escaped_slash", "^(https?):\\/\\/"),
    ("lazy_quantifier", "a.*?b"),
    ("nested_groups", "(a(b)?c)*"),
    ("class_shorthand", "[\\s\\S]*"),
    ("escaped_metachar", "\\(\\d+\\)"),
)

# Strings that are NOT valid ECMA 262 regular expressions and therefore MUST be
# rejected when constrained by `format: regex`.
_REGEX_ECMA262_INVALID = (
    ("unterminated_class", "[unclosed"),
    ("unterminated_group", "(unclosed"),
    ("reversed_quantifier", "a{3,2}"),
    ("trailing_backslash", "\\"),
    ("leading_quantifier", "*abc"),
    ("unmatched_paren", "a)"),
    ("dangling_quantifier", "a**"),
)


class TestCaseTestOp6Validation_RegexEcma262(HttpRunner):
    """OP#6 - Enforce the Draft-07 `regex` format as an ECMA 262 assertion.

    README §9.2 and ADR-0005 require `regex` to be asserted on string values:
    a value is valid only when it is a regular expression valid according to the
    ECMA 262 regular expression dialect. Valid patterns must pass; strings that
    are not valid ECMA 262 regular expressions must be rejected.
    """
    config = Config("OP#6 Extended - Regex ECMA 262 Conformance").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        """Run the test steps."""
        super().test_start()

    teststeps = [
        _register(
            f"gts://{_REGEX_ECMA262_TYPE_ID}",
            _REGEX_ECMA262_SCHEMA,
            "register schema with regex format",
        ),
        *[
            _register_instance(
                {
                    "type": _REGEX_ECMA262_TYPE_ID,
                    "id": (
                        f"{_REGEX_ECMA262_TYPE_ID}"
                        f"x.test6._.regex_valid_{label}.v1.0"
                    ),
                    "regexValue": pattern,
                },
                f"register instance with valid ECMA 262 regex ({label})",
            )
            for label, pattern in _REGEX_ECMA262_VALID
        ],
        *[
            _validate_instance(
                (
                    f"{_REGEX_ECMA262_TYPE_ID}"
                    f"x.test6._.regex_valid_{label}.v1.0"
                ),
                True,
                f"accept valid ECMA 262 regex ({label})",
            )
            for label, _ in _REGEX_ECMA262_VALID
        ],
        *[
            _register_instance(
                {
                    "type": _REGEX_ECMA262_TYPE_ID,
                    "id": (
                        f"{_REGEX_ECMA262_TYPE_ID}"
                        f"x.test6._.regex_invalid_{label}.v1.0"
                    ),
                    "regexValue": pattern,
                },
                f"register instance with invalid ECMA 262 regex ({label})",
            )
            for label, pattern in _REGEX_ECMA262_INVALID
        ],
        *[
            _validate_instance(
                (
                    f"{_REGEX_ECMA262_TYPE_ID}"
                    f"x.test6._.regex_invalid_{label}.v1.0"
                ),
                False,
                f"reject invalid ECMA 262 regex ({label})",
            )
            for label, _ in _REGEX_ECMA262_INVALID
        ],
    ]


class TestCaseTestOp6Validation_UuidRejectsGtsId(HttpRunner):
    config = Config("OP#6 Extended - UUID Format Validation").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.formats.uuid.v1~",
            {
                "type": "object",
                "required": ["uuidValue"],
                "properties": {"uuidValue": {"type": "string", "format": "uuid"}},
            },
            "register UUID format schema",
        ),
        _register_instance(
            {
                "type": "gts.x.test6.formats.uuid.v1~",
                "id": "gts.x.test6.formats.uuid.v1~x.test6._.gts_id.v1.0",
                "uuidValue": "gts.x.test6.formats.uuid.v1~550e8400-e29b-41d4-a716-446655440000",
            },
            "register instance with GTS ID in UUID field",
        ),
        _validate_instance(
            "gts.x.test6.formats.uuid.v1~x.test6._.gts_id.v1.0",
            False,
            "reject GTS ID in UUID field",
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
# Extended JSON Schema constraint tests — negative cases
#
# The positive constraint tests above (enum / nested / array / minimum) only
# prove that a *conforming* instance passes. On their own they cannot detect a
# no-op validator that always returns ok=True. These tests supply the missing
# violating instances so each keyword is exercised in both directions. Standard
# `format` keywords already have negative coverage in
# TestCaseTestOp6Validation_StandardFormats, so they are not repeated here.
# ---------------------------------------------------------------------------


class TestCaseTestOp6Validation_EnumConstraints_Invalid(HttpRunner):
    """OP#6 - An instance whose value is outside the schema enum MUST fail."""

    config = Config("OP#6 Extended - Enum Validation (invalid)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.enuminvalid.status.v1~",
            {
                "type": "object",
                "required": ["statusId", "status"],
                "properties": {
                    "statusId": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "approved", "rejected"],
                    },
                },
            },
            "register schema with enum",
        ),
        _register_instance(
            {
                "type": "gts.x.test6.enuminvalid.status.v1~",
                "id": "gts.x.test6.enuminvalid.status.v1~x.test6._.bad_status.v1",
                "statusId": "STATUS-001",
                "status": "escalated",
            },
            "register instance with out-of-enum status",
        ),
        _validate_instance(
            "gts.x.test6.enuminvalid.status.v1~x.test6._.bad_status.v1",
            False,
            "reject instance whose status is not in the enum",
        ),
    ]


class TestCaseTestOp6Validation_ArrayConstraints_Invalid(HttpRunner):
    """OP#6 - Arrays violating minItems / maxItems MUST fail validation."""

    config = Config("OP#6 Extended - Array Constraints (invalid)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.arrayinvalid.tags.v1~",
            {
                "type": "object",
                "required": ["itemId", "tags"],
                "properties": {
                    "itemId": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 3,
                        "items": {"type": "string"},
                    },
                },
            },
            "register schema with array constraints",
        ),
        # Below minItems (empty array).
        _register_instance(
            {
                "type": "gts.x.test6.arrayinvalid.tags.v1~",
                "id": "gts.x.test6.arrayinvalid.tags.v1~x.test6._.too_few.v1",
                "itemId": "ITEM-001",
                "tags": [],
            },
            "register instance with too few tags",
        ),
        _validate_instance(
            "gts.x.test6.arrayinvalid.tags.v1~x.test6._.too_few.v1",
            False,
            "reject instance below minItems",
        ),
        # Above maxItems (four entries).
        _register_instance(
            {
                "type": "gts.x.test6.arrayinvalid.tags.v1~",
                "id": "gts.x.test6.arrayinvalid.tags.v1~x.test6._.too_many.v1",
                "itemId": "ITEM-002",
                "tags": ["a", "b", "c", "d"],
            },
            "register instance with too many tags",
        ),
        _validate_instance(
            "gts.x.test6.arrayinvalid.tags.v1~x.test6._.too_many.v1",
            False,
            "reject instance above maxItems",
        ),
    ]


class TestCaseTestOp6Validation_NestedObjects_Invalid(HttpRunner):
    """OP#6 - Violations inside nested objects / arrays MUST fail validation.

    Covers a missing deeply-nested required property and a numeric `minimum`
    violation on an array item, neither of which is exercised by the positive
    nested-object test.
    """

    config = Config("OP#6 Extended - Nested Object Validation (invalid)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.nestedinvalid.order.v1~",
            {
                "type": "object",
                "required": ["orderId", "customer", "items"],
                "properties": {
                    "orderId": {"type": "string"},
                    "customer": {
                        "type": "object",
                        "required": ["customerId", "address"],
                        "properties": {
                            "customerId": {"type": "string"},
                            "address": {
                                "type": "object",
                                "required": ["street", "country"],
                                "properties": {
                                    "street": {"type": "string"},
                                    "country": {"type": "string"},
                                },
                            },
                        },
                    },
                    "items": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["sku", "quantity"],
                            "properties": {
                                "sku": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                            },
                        },
                    },
                },
            },
            "register nested schema",
        ),
        # Missing deeply-nested required property (customer.address.country).
        _register_instance(
            {
                "type": "gts.x.test6.nestedinvalid.order.v1~",
                "id": "gts.x.test6.nestedinvalid.order.v1~x.test6._.no_country.v1",
                "orderId": "ORD-1",
                "customer": {
                    "customerId": "CUST-1",
                    "address": {"street": "123 Main St"},
                },
                "items": [{"sku": "SKU-1", "quantity": 1}],
            },
            "register instance missing nested required country",
        ),
        _validate_instance(
            "gts.x.test6.nestedinvalid.order.v1~x.test6._.no_country.v1",
            False,
            "reject instance missing customer.address.country",
        ),
        # Numeric minimum violation on an array item (quantity 0).
        _register_instance(
            {
                "type": "gts.x.test6.nestedinvalid.order.v1~",
                "id": "gts.x.test6.nestedinvalid.order.v1~x.test6._.bad_qty.v1",
                "orderId": "ORD-2",
                "customer": {
                    "customerId": "CUST-2",
                    "address": {"street": "1 Elm St", "country": "USA"},
                },
                "items": [{"sku": "SKU-2", "quantity": 0}],
            },
            "register instance with quantity below minimum",
        ),
        _validate_instance(
            "gts.x.test6.nestedinvalid.order.v1~x.test6._.bad_qty.v1",
            False,
            "reject instance whose item quantity is below minimum",
        ),
    ]


class TestCaseTestOp6Validation_AdditionalPropertiesRejected(HttpRunner):
    """OP#6 - An instance with an undeclared property MUST fail a closed schema.

    The envelope schemas set ``additionalProperties: false`` but no test sends
    an instance carrying an unexpected top-level property. This proves the
    closed-model constraint is actually enforced on stored instances.
    """

    config = Config("OP#6 Extended - additionalProperties enforced").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.closed.event.v1~",
            {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
                "additionalProperties": False,
            },
            "register closed schema",
        ),
        _register_instance(
            {
                "type": "gts.x.test6.closed.event.v1~",
                "id": "gts.x.test6.closed.event.v1~x.test6._.extra_prop.v1",
                "name": "valid",
                "unexpected": "value",
            },
            "register instance with an undeclared property",
        ),
        _validate_instance(
            "gts.x.test6.closed.event.v1~x.test6._.extra_prop.v1",
            False,
            "reject instance carrying an undeclared property",
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

    def test_start(self):
        super().test_start()

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

    def test_start(self):
        super().test_start()

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

    def test_start(self):
        super().test_start()

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

    def test_start(self):
        super().test_start()

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

    def test_start(self):
        super().test_start()

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


# ---------------------------------------------------------------------------
# Unknown x-gts-* extension keyword tests
#
# The GTS Type Schema is a JSON Schema document annotated with the GTS-specific
# keywords in the reserved `x-gts-*` namespace (README §Terminology / §9). The
# specification defines exactly five such keywords:
#
# - x-gts-ref            (§9.6)
# - x-gts-traits-schema  (§9.7)
# - x-gts-traits         (§9.7)
# - x-gts-final          (§9.11)
# - x-gts-abstract       (§9.11)
#
# Any other `x-gts-*` key is an **unknown extension** — a typo (`x-gts-trait`),
# a dropped/experimental keyword (`x-gts-traits-completeness`,
# `x-gts-trait-merge`), or a vendor keyword that never became part of the spec.
# Because the `x-gts-*` prefix is reserved for GTS semantics, an implementation
# MUST NOT silently ignore an unknown one: when validation is enabled
# (`?validate=true`) registration MUST fail fast (422) rather than accept a
# schema whose GTS meaning the registry cannot interpret.
#
# These tests assert that:
# - a schema exercising every supported `x-gts-*` keyword in a valid position is
#   accepted with validation on (positive control);
# - an unknown `x-gts-*` keyword is rejected wherever it appears — at the document
#   top level, nested in a subschema (`properties` / `$defs` / `allOf` entry), and
#   as a near-miss typo of a real keyword.
#
# The rule is about the *keyword name* being outside the supported set; it is
# orthogonal to the placement rule for the four document-level keywords
# (§9.7.1/§9.11, covered by test_xgts_keyword_placement.py).
# ---------------------------------------------------------------------------

_XGTS_SCHEMA = "http://json-schema.org/draft-07/schema#"


def _register_validated(gts_id, body, expected_status, label):
    """POST /entities?validate=true and assert the resulting status code.

    `body` is the schema body without `$id`/`$schema`; both are injected here.
    """
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_params(**{"validate": "true"})
        .with_json({
            **body,
            "$$id": gts_id,
            "$$schema": _XGTS_SCHEMA,
        })
        .validate()
        .assert_equal("status_code", expected_status)
    )


# Positive control — every supported x-gts-* keyword is accepted


class TestCaseSupportedExtensions_Accepted(HttpRunner):
    """All five supported x-gts-* keywords, in valid positions, register cleanly.

    Positive control: proves the rejection tests below fail because of the
    *unknown* keyword name, not because validation rejects x-gts-* wholesale.
    Covers x-gts-abstract, x-gts-traits-schema and x-gts-ref on the base, and
    x-gts-final and x-gts-traits on the derived type.
    """

    config = Config("unknown-ext: supported keywords accepted").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_validated(
            "gts://gts.x.testext.supported.base.v1~",
            {
                "type": "object",
                "x-gts-abstract": True,
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"retention": {"type": "string"}},
                },
                "properties": {
                    "id": {"type": "string"},
                    "ownerRef": {"type": "string", "x-gts-ref": "gts.*"},
                },
            },
            200,
            "register base using x-gts-abstract, x-gts-traits-schema, x-gts-ref",
        ),
        Step(
            RunRequest("register derived using x-gts-final and x-gts-traits")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testext.supported.base.v1~x.testext._.leaf.v1~",
                "$$schema": _XGTS_SCHEMA,
                "type": "object",
                "x-gts-final": True,
                "x-gts-traits": {"retention": "P30D"},
                "allOf": [{"$$ref": "gts://gts.x.testext.supported.base.v1~"}],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


# Unknown x-gts-* keyword at the document top level


class TestCaseUnknown_TopLevelRejected(HttpRunner):
    """An unknown x-gts-* keyword at the top level MUST be rejected."""

    config = Config("unknown-ext: unknown top-level keyword rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_validated(
            "gts://gts.x.testext.toplevel.base.v1~",
            {
                "type": "object",
                "x-gts-bogus": True,
                "properties": {"id": {"type": "string"}},
            },
            422,
            "register schema with unknown x-gts-bogus at top level should be rejected",
        ),
    ]


# Unknown x-gts-* keyword nested in subschemas


class TestCaseUnknown_InsidePropertiesRejected(HttpRunner):
    """An unknown x-gts-* keyword nested in a `properties` subschema MUST be rejected."""

    config = Config("unknown-ext: unknown keyword inside properties rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_validated(
            "gts://gts.x.testext.prop.base.v1~",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "widget": {"type": "string", "x-gts-widget": "dropdown"},
                },
            },
            422,
            "register schema with unknown x-gts-widget inside a property should be rejected",
        ),
    ]


class TestCaseUnknown_InsideDefsRejected(HttpRunner):
    """An unknown x-gts-* keyword nested in a `definitions` entry MUST be rejected."""

    config = Config("unknown-ext: unknown keyword inside definitions rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_validated(
            "gts://gts.x.testext.defs.base.v1~",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "definitions": {
                    "Sub": {"type": "object", "x-gts-experimental": True},
                },
            },
            422,
            "register schema with unknown x-gts-experimental inside definitions should be rejected",
        ),
    ]


class TestCaseUnknown_InsideAllOfRejected(HttpRunner):
    """An unknown x-gts-* keyword nested in an `allOf` entry MUST be rejected."""

    config = Config("unknown-ext: unknown keyword inside allOf rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.testext.allof.base.v1~",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            },
            "register base for allOf derivation",
        ),
        Step(
            RunRequest("register derived with unknown x-gts-* inside allOf should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testext.allof.base.v1~x.testext._.derived.v1~",
                "$$schema": _XGTS_SCHEMA,
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testext.allof.base.v1~"},
                    {"type": "object", "x-gts-policy": "strict"},
                ],
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


# Near-miss typos of supported keywords


class TestCaseUnknown_TraitsTypoRejected(HttpRunner):
    """A near-miss typo of a supported keyword (x-gts-trait) MUST be rejected.

    `x-gts-trait` (singular) is not `x-gts-traits`; treating it as a synonym
    would silently drop the author's intended trait values, so it must fail.
    """

    config = Config("unknown-ext: x-gts-trait typo rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_validated(
            "gts://gts.x.testext.typo.base.v1~",
            {
                "type": "object",
                "x-gts-trait": {"retention": "P30D"},
                "properties": {"id": {"type": "string"}},
            },
            422,
            "register schema with x-gts-trait (typo of x-gts-traits) should be rejected",
        ),
    ]


class TestCaseUnknown_RefTypoRejected(HttpRunner):
    """A near-miss typo of x-gts-ref (x-gts-reference) inside a property MUST be rejected."""

    config = Config("unknown-ext: x-gts-reference typo rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_validated(
            "gts://gts.x.testext.reftypo.base.v1~",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "ownerRef": {"type": "string", "x-gts-reference": "gts.*"},
                },
            },
            422,
            "register schema with x-gts-reference (typo of x-gts-ref) should be rejected",
        ),
    ]

# ---------------------------------------------------------------------------
# /validate-json tests
# ---------------------------------------------------------------------------

def _raw_json_schema(type_id, required_field="name"):
    return {
        "$$id": f"gts://{type_id}",
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [required_field],
        "properties": {required_field: {"type": "string"}},
        "additionalProperties": False,
    }


def _assert_not_stored(gts_id):
    return Step(
        RunRequest("transient entity must not be stored")
        .get(f"/entities/{gts_id}")
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", False)
    )


class TestCaseOp6ValidateJson_AutoBaseSchema(HttpRunner):
    config = Config("OP#6 validate-json: transient base schema").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("validate a base schema without registration")
            .post("/validate-json")
            .with_json(_raw_json_schema("gts.x.test6json._.auto_base.v1~"))
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.is_type_schema", True)
        ),
        _assert_not_stored("gts.x.test6json._.auto_base.v1~"),
    ]


class TestCaseOp6ValidateJson_AutoInvalidSchema(HttpRunner):
    config = Config("OP#6 validate-json: invalid transient schema").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject an invalid transient schema")
            .post("/validate-json")
            .with_json({
                "$$id": "gts://gts.x.test6json._.invalid_schema.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": 1,
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", True)
            .assert_contains("body.error", "JSON Schema validation failed")
        ),
        _assert_not_stored("gts.x.test6json._.invalid_schema.v1~"),
    ]


class TestCaseOp6ValidateJson_AutoDerivedSchema(HttpRunner):
    config = Config("OP#6 validate-json: transient derived schema").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.derived_base.v1~", {
            "type": "object",
            "properties": {"base": {"type": "string"}},
        }),
        Step(
            RunRequest("validate a derived schema without registration")
            .post("/validate-json")
            .with_json({
                "$$id": "gts://gts.x.test6json._.derived_base.v1~x.test6json._.derived.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test6json._.derived_base.v1~"}],
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.is_type_schema", True)
        ),
        _assert_not_stored("gts.x.test6json._.derived_base.v1~x.test6json._.derived.v1~"),
    ]


class TestCaseOp6ValidateJson_AutoDerivedSchemaMissingParent(HttpRunner):
    config = Config("OP#6 validate-json: derived schema missing parent").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject a derived schema whose parent is not registered")
            .post("/validate-json")
            .with_json({
                "$$id": "gts://gts.x.test6json._.missing_base.v1~x.test6json._.derived.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", True)
            .assert_contains("body.error", "Parent GTS Type Schema not found")
        ),
    ]


class TestCaseOp6ValidateJson_AutoInstance(HttpRunner):
    config = Config("OP#6 validate-json: transient instance").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.auto_instance.v1~", {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }),
        Step(
            RunRequest("validate a transient instance using its declared type")
            .post("/validate-json")
            .with_json({
                "id": "gts.x.test6json._.auto_instance.v1~x.test6json._.item.v1",
                "type": "gts.x.test6json._.auto_instance.v1~",
                "name": "valid",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.is_type_schema", False)
        ),
        _assert_not_stored("gts.x.test6json._.auto_instance.v1~x.test6json._.item.v1"),
    ]


class TestCaseOp6ValidateJson_AutoInvalidInstance(HttpRunner):
    config = Config("OP#6 validate-json: invalid transient instance").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.auto_invalid.v1~", {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }),
        Step(
            RunRequest("reject an invalid transient instance")
            .post("/validate-json")
            .with_json({
                "id": "gts.x.test6json._.auto_invalid.v1~x.test6json._.item.v1",
                "type": "gts.x.test6json._.auto_invalid.v1~",
                "name": 1,
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", False)
            .assert_contains("body.error", "is not of type 'string'")
        ),
        _assert_not_stored("gts.x.test6json._.auto_invalid.v1~x.test6json._.item.v1"),
    ]


class TestCaseOp6ValidateJson_AutoIdlessInstance(HttpRunner):
    config = Config("OP#6 validate-json: idless transient instance").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.idless.v1~", {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }),
        Step(
            RunRequest("validate an idless transient instance")
            .post("/validate-json")
            .with_json({"type": "gts.x.test6json._.idless.v1~", "name": "valid"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.is_type_schema", False)
        ),
    ]


class TestCaseOp6ValidateJson_AutoInstanceMissingType(HttpRunner):
    config = Config("OP#6 validate-json: instance without type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject a transient instance without a type")
            .post("/validate-json")
            .with_json({"id": "gts.x.test6json._.no_type.v1"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", False)
            .assert_contains("body.error", "Unable to determine instance type")
        ),
    ]


class TestCaseOp6ValidateJson_ExplicitType(HttpRunner):
    config = Config("OP#6 validate-json: explicit base type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.explicit.v1~", {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }),
        Step(
            RunRequest("validate a transient object against an explicit type")
            .post("/validate-json/gts.x.test6json._.explicit.v1~")
            .with_json({
                "id": "gts.x.test6json._.explicit.v1~x.test6json._.item.v1",
                "name": "valid",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.is_type_schema", False)
            .assert_equal("body.type_id", "gts.x.test6json._.explicit.v1~")
        ),
        _assert_not_stored("gts.x.test6json._.explicit.v1~x.test6json._.item.v1"),
    ]


class TestCaseOp6ValidateJson_ExplicitTypeInvalidInstance(HttpRunner):
    config = Config("OP#6 validate-json: invalid explicit type instance").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.explicit_invalid.v1~", {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }),
        Step(
            RunRequest("reject an invalid transient object against an explicit type")
            .post("/validate-json/gts.x.test6json._.explicit_invalid.v1~")
            .with_json({"name": 1})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.is_type_schema", False)
            .assert_contains("body.error", "is not of type 'string'")
        ),
    ]


class TestCaseOp6ValidateJson_ExplicitDerivedType(HttpRunner):
    config = Config("OP#6 validate-json: explicit derived type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.explicit_derived.v1~", {
            "type": "object",
            "required": ["base"],
            "properties": {"base": {"type": "string"}},
        }),
        _register("gts://gts.x.test6json._.explicit_derived.v1~x.test6json._.child.v1~", {
            "type": "object",
            "allOf": [{"$$ref": "gts://gts.x.test6json._.explicit_derived.v1~"}],
            "required": ["child"],
            "properties": {"child": {"type": "string"}},
        }),
        Step(
            RunRequest("validate an object against an explicit derived type")
            .post("/validate-json/gts.x.test6json._.explicit_derived.v1~x.test6json._.child.v1~")
            .with_json({"base": "base", "child": "child"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.type_id", "gts.x.test6json._.explicit_derived.v1~x.test6json._.child.v1~")
        ),
    ]


class TestCaseOp6ValidateJson_ExplicitSchemaWithoutEmbeddedIdentity(HttpRunner):
    config = Config("OP#6 validate-json: explicit schema without embedded identity").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register an explicit schema without $id or root type")
            .post("/type-schemas")
            .with_json({
                "type_id": "gts.x.test6json._.external_identity.v1~",
                "type_schema": {
                    "properties": {"prop": {"type": "string"}},
                },
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("validate an object against the explicit schema")
            .post("/validate-json/gts.x.test6json._.external_identity.v1~")
            .with_json({"prop": "valid"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.type_id", "gts.x.test6json._.external_identity.v1~")
        ),
        Step(
            RunRequest("reject a non-matching object against the explicit schema")
            .post("/validate-json/gts.x.test6json._.external_identity.v1~")
            .with_json({"prop": 1})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "is not of type 'string'")
        ),
    ]


class TestCaseOp6ValidateJson_MalformedExplicitType(HttpRunner):
    config = Config("OP#6 validate-json: malformed explicit type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject a malformed explicit type")
            .post("/validate-json/not-a-gts-type")
            .with_json({"name": "valid"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "Invalid GTS Type Schema ID")
        ),
    ]


class TestCaseOp6ValidateJson_UnknownExplicitType(HttpRunner):
    config = Config("OP#6 validate-json: unknown explicit type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject an explicit type that is not registered")
            .post("/validate-json/gts.x.test6json._.unknown.v1~")
            .with_json({"name": "valid"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "GTS Type Schema not found")
        ),
    ]


class TestCaseOp6ValidateJson_ExplicitNonSchemaType(HttpRunner):
    config = Config("OP#6 validate-json: explicit non-schema type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject an explicit GTS instance ID as a type")
            .post("/validate-json/gts.x.test6json._.not_schema.v1")
            .with_json({"name": "valid"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "must be GTS Type schema")
        ),
    ]


class TestCaseOp6ValidateJson_ExplicitTypeMismatch(HttpRunner):
    config = Config("OP#6 validate-json: explicit type mismatch").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.expected.v1~", {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }),
        _register("gts://gts.x.test6json._.declared.v1~", {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }),
        Step(
            RunRequest("reject a body whose declared type conflicts with the path type")
            .post("/validate-json/gts.x.test6json._.expected.v1~")
            .with_json({"type": "gts.x.test6json._.declared.v1~", "name": "valid"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "does not match path type")
        ),
    ]


class TestCaseOp6ValidateJson_ExplicitTypeRejectsSchema(HttpRunner):
    config = Config("OP#6 validate-json: schema with explicit type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test6json._.schema_path.v1~", {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }),
        Step(
            RunRequest("reject a schema body on the explicit type route")
            .post("/validate-json/gts.x.test6json._.schema_path.v1~")
            .with_json(_raw_json_schema("gts.x.test6json._.rejected_schema.v1~"))
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_contains("body.error", "only accepts instance JSON")
        ),
        _assert_not_stored("gts.x.test6json._.rejected_schema.v1~"),
    ]


class TestCaseOp6ValidateJson_NonObjectBody(HttpRunner):
    config = Config("OP#6 validate-json: non-object request body").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("reject a non-object JSON validation body")
            .post("/validate-json")
            .with_json(["not", "an", "object"])
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseOp6ValidationErrorPath(HttpRunner):
    config = Config(
        "OP#6 validation errors do not expose file URI references"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.error.path.v1~",
            {
                "type": "object",
                "required": ["id", "type", "address"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"const": "gts.x.test6.error.path.v1~"},
                    "address": {"type": "string", "format": "ipv4"},
                },
            },
            "register schema for portable validation error",
        ),
        _register_instance(
            {
                "id": "gts.x.test6.error.path.v1~x.test6._.invalid.v1",
                "type": "gts.x.test6.error.path.v1~",
                "address": "999.999.999.999",
            },
            "register instance with invalid address",
        ),
        Step(
            RunRequest("validate invalid address without an absolute file path")
            .post("/validate-instance")
            .with_json(
                {"instance_id": "gts.x.test6.error.path.v1~x.test6._.invalid.v1"}
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_regex_match("body.error", r"(?si)^(?!.*file://).*$")
        ),
    ]


class TestCaseOp6InstanceResubmission(HttpRunner):
    config = Config(
        "OP#6 instance resubmission is immutable"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.resubmit.instance.v1~",
            {
                "type": "object",
                "required": ["id", "type", "value"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"const": "gts.x.test6.resubmit.instance.v1~"},
                    "value": {"type": "string"},
                },
            },
            "register schema for instance resubmission",
        ),
        _register_instance(
            {
                "id": "gts.x.test6.resubmit.instance.v1~x.test6._.example.v1",
                "type": "gts.x.test6.resubmit.instance.v1~",
                "value": "initial",
            },
            "register instance initially",
        ),
        _register_instance(
            {
                "id": "gts.x.test6.resubmit.instance.v1~x.test6._.example.v1",
                "type": "gts.x.test6.resubmit.instance.v1~",
                "value": "initial",
            },
            "resubmit identical instance",
        ),
        Step(
            RunRequest("reject changed instance content")
            .post("/entities")
            .with_json(
                {
                    "id": "gts.x.test6.resubmit.instance.v1~x.test6._.example.v1",
                    "type": "gts.x.test6.resubmit.instance.v1~",
                    "value": "changed",
                }
            )
            .validate()
            .assert_equal("status_code", 409)
        ),
    ]


class TestCaseOp6TypeResubmission(HttpRunner):
    config = Config(
        "OP#6 type resubmission is immutable"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test6.resubmit.type.v1~",
            {
                "type": "object",
                "properties": {"value": {"type": "string"}},
            },
            "register type schema initially",
        ),
        _register(
            "gts://gts.x.test6.resubmit.type.v1~",
            {
                "type": "object",
                "properties": {"value": {"type": "string"}},
            },
            "resubmit identical type schema",
        ),
        Step(
            RunRequest("reject changed type schema")
            .post("/entities")
            .with_json(
                {
                    "$$id": "gts://gts.x.test6.resubmit.type.v1~",
                    "$$schema": "http://json-schema.org/draft-07/schema#",
                    "type": "object",
                    "properties": {"value": {"type": "integer"}},
                }
            )
            .validate()
            .assert_equal("status_code", 409)
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp6ValidateInstance_ValidInstance().test_start()
