from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


# ---------------------------------------------------------------------------
# Helper functions to reduce boilerplate across repetitive test patterns
# ---------------------------------------------------------------------------

def _register(gts_id, schema_body, label="register schema"):
    """Register a schema via POST /entities."""
    body = {
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        **schema_body,
    }
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


def _register_derived(gts_id, base_ref, overlay, label="register derived"):
    """Register a derived schema that uses allOf with a $$ref."""
    body = {
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "allOf": [
            {"$$ref": base_ref},
            overlay,
        ],
    }
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


def _validate_schema(schema_id, expect_ok, label="validate schema"):
    """Validate a derived schema via POST /validate-schema."""
    step = (
        RunRequest(label)
        .post("/validate-schema")
        .with_json({"schema_id": schema_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    return Step(step)


def _make_2level_constraint_drop_steps(
    ns, prop_name, prop_type, constraint_kw, constraint_val,
    extra_base=None,
):
    """Build teststeps for a 2-level test where derived drops a keyword.

    The base schema has one property with a constraint; the derived
    schema restates the property without that constraint keyword.
    Validation must fail (constraint loosened).
    """
    base_id = f"gts://gts.x.test12.drop.{ns}.v1~"
    derived_suffix = f"x.test12._.no_{ns}.v1~"
    derived_id = base_id + derived_suffix
    schema_id = f"gts.x.test12.drop.{ns}.v1~" + derived_suffix

    base_prop = {"type": prop_type, constraint_kw: constraint_val}
    if extra_base:
        base_prop.update(extra_base)

    derived_prop = {"type": prop_type}
    if extra_base:
        derived_prop.update(extra_base)

    return [
        _register(base_id, {
            "type": "object",
            "required": [prop_name],
            "properties": {prop_name: base_prop},
        }, f"register base with {constraint_kw}"),
        _register_derived(
            derived_id, base_id,
            {"type": "object", "properties": {
                prop_name: derived_prop,
            }},
            f"register derived dropping {constraint_kw}",
        ),
        _validate_schema(
            schema_id, False,
            f"validate should fail - {constraint_kw} dropped",
        ),
    ]


def _make_3level_const_steps(
    ns, field_name, field_type, l2_const, l3_const, expect_l3_ok,
):
    """Build teststeps for a 3-level const conflict or idempotent test.

    Base has a plain typed field. L2 adds const=l2_const (valid).
    L3 sets const=l3_const. If l3_const != l2_const → fail;
    if equal → pass (idempotent).
    """
    base_id = f"gts://gts.x.test12.{ns}.item.v1~"
    l2_suffix = f"x.test12._.l2_{ns}.v1~"
    l3_suffix = f"x.test12._.l3_{ns}.v1~"
    l2_id = base_id + l2_suffix
    l3_id = l2_id + l3_suffix
    l2_schema_id = f"gts.x.test12.{ns}.item.v1~" + l2_suffix
    l3_schema_id = l2_schema_id + l3_suffix

    return [
        _register(base_id, {
            "type": "object",
            "required": ["itemId", field_name],
            "properties": {
                "itemId": {"type": "string"},
                field_name: {"type": field_type},
            },
        }, "register base schema"),
        _register_derived(
            l2_id, base_id,
            {"type": "object", "properties": {
                field_name: {"type": field_type, "const": l2_const},
            }},
            f"register L2 with const {l2_const!r}",
        ),
        _validate_schema(l2_schema_id, True, "validate L2"),
        _register_derived(
            l3_id, l2_id,
            {"type": "object", "properties": {
                field_name: {"type": field_type, "const": l3_const},
            }},
            f"register L3 with const {l3_const!r}",
        ),
        _validate_schema(l3_schema_id, expect_l3_ok, "validate L3"),
    ]


def _make_3level_loosening_steps(
    ns, field_name, field_type, base_constraint,
    l2_constraint, l3_constraint, keyword,
    extra_prop=None, expect_l3_ok=False,
):
    """Build teststeps for a 3-level constraint cascade test.

    Base has keyword=base_constraint, L2 tightens to l2_constraint,
    L3 sets l3_constraint. L2 must pass. L3 result controlled by
    expect_l3_ok (default False = loosening must fail).
    """
    base_id = f"gts://gts.x.test12.{ns}.item.v1~"
    l2_suffix = f"x.test12._.l2_{ns}.v1~"
    l3_suffix = f"x.test12._.l3_{ns}.v1~"
    l2_id = base_id + l2_suffix
    l3_id = l2_id + l3_suffix
    l2_schema_id = f"gts.x.test12.{ns}.item.v1~" + l2_suffix
    l3_schema_id = l2_schema_id + l3_suffix

    base_prop = {"type": field_type, keyword: base_constraint}
    l2_prop = {"type": field_type, keyword: l2_constraint}
    l3_prop = {"type": field_type, keyword: l3_constraint}
    if extra_prop:
        base_prop.update(extra_prop)
        l2_prop.update(extra_prop)
        l3_prop.update(extra_prop)

    return [
        _register(base_id, {
            "type": "object",
            "required": ["itemId", field_name],
            "properties": {
                "itemId": {"type": "string"},
                field_name: base_prop,
            },
        }, f"register base with {keyword} {base_constraint}"),
        _register_derived(
            l2_id, base_id,
            {"type": "object", "properties": {
                field_name: l2_prop,
            }},
            f"register L2 tightening {keyword} to {l2_constraint}",
        ),
        _validate_schema(l2_schema_id, True, "validate L2"),
        _register_derived(
            l3_id, l2_id,
            {"type": "object", "properties": {
                field_name: l3_prop,
            }},
            f"register L3 loosening {keyword} to {l3_constraint}",
        ),
        _validate_schema(l3_schema_id, expect_l3_ok, "validate L3"),
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCaseTestOp12SchemaValidation_DerivedSchemaFullyMatches(HttpRunner):
    """OP#12 - Schema vs Schema: Derived schema fully matches base"""
    config = Config("OP#12 - Fully Matching Derived Schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12a.base.user.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["userId", "email"],
                "properties": {
                    "userId": {"type": "string", "format": "uuid"},
                    "email": {"type": "string", "format": "email"},
                    "tier": {"type": "string", "maxLength": 100}
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema that matches base")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12a.base.user.v1~"
                    "x.test12a._.premium_user.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12a.base.user.v1~"},
                    {
                        "type": "object",
                        "required": ["tier"],
                        "properties": {
                            "tier": {
                                "type": "string",
                                "enum": ["gold", "platinum"]
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate derived schema against base")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12a.base.user.v1~x.test12a._.premium_user.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_DerivedSchemaAddsNewFieldsToBaseOne(HttpRunner):
    """OP#12 - Schema vs Schema: Derived schema adds new fields to base"""
    config = Config("OP#12 - Derived Schema Adds New Fields To Base").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12b.base.user.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["userId", "email"],
                "properties": {
                    "userId": {"type": "string", "format": "uuid"},
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string", "maxLength": 100}
                },
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema that matches base")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12b.base.user.v1~"
                    "x.test12b._.premium_user.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12b.base.user.v1~"},
                    {
                        "type": "object",
                        "required": ["subscriptionTier"],
                        "properties": {
                            "subscriptionTier": {
                                "type": "string",
                                "enum": ["gold", "platinum"]
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate derived schema against base")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12b.base.user.v1~x.test12b._.premium_user.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_AdditionalPropertiesFalse(
    HttpRunner
):
    """OP#12 - Schema vs Schema: Base has additionalProperties false"""
    config = Config(
        "OP#12 - additionalProperties False Violation"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register closed base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.closed.account.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["accountId", "email"],
                "properties": {
                    "accountId": {"type": "string", "format": "uuid"},
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string", "maxLength": 100}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema adding properties")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.closed.account.v1~"
                    "x.test12._.premium_account.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.closed.account.v1~"},
                    {
                        "type": "object",
                        "required": ["tier"],
                        "properties": {
                            "tier": {
                                "type": "string",
                                "enum": ["gold", "platinum"]
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate should fail - base forbids extra properties")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.closed.account.v1~"
                    "x.test12._.premium_account.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12SchemaValidation_CloseOpenModel(HttpRunner):
    """OP#12 - Schema vs Schema: Derived closes an open model"""
    config = Config(
        "OP#12 - Close Open Model"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register open base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.close.user.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["userId", "email"],
                "properties": {
                    "userId": {"type": "string", "format": "uuid"},
                    "email": {"type": "string", "format": "email"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema closing model")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.close.user.v1~"
                    "x.test12._.closed_user.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.close.user.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "userId": {
                                "type": "string",
                                "format": "uuid"
                            },
                            "email": {
                                "type": "string",
                                "format": "email"
                            }
                        },
                        "additionalProperties": False
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate derived schema should pass")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.close.user.v1~"
                    "x.test12._.closed_user.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_NestedAdditionalPropertiesFalse(
    HttpRunner
):
    """OP#12 - Schema vs Schema: Nested additionalProperties false"""
    config = Config(
        "OP#12 - Nested additionalProperties False"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with closed nested object")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.nested.closed.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["profileId", "profile"],
                "properties": {
                    "profileId": {"type": "string"},
                    "profile": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "age": {
                                "type": "integer",
                                "minimum": 0
                            }
                        },
                        "additionalProperties": False
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema adding nested property")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.nested.closed.v1~"
                    "x.test12._.profile_plus.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.nested.closed.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "profile": {
                                "type": "object",
                                "properties": {
                                    "nickname": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate derived schema should fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.nested.closed.v1~"
                    "x.test12._.profile_plus.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12SchemaValidation_InvalidDerivedSchema(
    HttpRunner
):
    """OP#12 - Schema vs Schema: Invalid derived schema"""
    config = Config("OP#12 - Invalid Derived Schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with required fields")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.base.order.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["orderId", "customerId", "total"],
                "properties": {
                    "orderId": {"type": "string"},
                    "customerId": {"type": "string"},
                    "total": {"type": "number", "minimum": 0}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema contradicting base")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.base.order.v1~"
                    "x.test12._.bad_order.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.base.order.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "customerId": False
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate derived schema should fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.base.order.v1~x.test12._.bad_order.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12SchemaValidation_DerivedSchemaConstraintTighten(
    HttpRunner
):
    """OP#12 - Schema vs Schema: Derived schema tightens constraints"""
    config = Config("OP#12 - Tightened Constraints").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with loose constraints")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.base.text.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["textId", "content"],
                "properties": {
                    "textId": {"type": "string"},
                    "content": {"type": "string", "maxLength": 1000},
                    "priority": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema with tighter constraints")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.base.text.v1~"
                    "x.test12._.short_text.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.base.text.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "maxLength": 500
                            },
                            "priority": {
                                "type": "integer",
                                "minimum": 10,
                                "maximum": 50
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate derived schema with tighter constraints")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.base.text.v1~x.test12._.short_text.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_DerivedSchemaConstraintLoosen(
    HttpRunner
):
    """OP#12 - Schema vs Schema: Derived schema loosens constraints"""
    config = Config("OP#12 - Loosened Constraints (Invalid)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with strict constraints")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.base.data.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["dataId"],
                "properties": {
                    "dataId": {"type": "string"},
                    "value": {"type": "string", "maxLength": 128}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema with looser constraints")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.base.data.v1~"
                    "x.test12._.loose_data.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.base.data.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string", "maxLength": 256}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate schema with looser constraints should fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.base.data.v1~x.test12._.loose_data.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12SchemaValidation_DerivedSpecifiesObject(HttpRunner):
    """OP#12 - Schema vs Schema: Base has object property,
    derived specifies it
    """
    config = Config(
        "OP#12 - Derived Specifies Base Object Property"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with object property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.objspec.event.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "payload"],
                "properties": {
                    "eventId": {"type": "string", "format": "uuid"},
                    "payload": {"type": "object"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema specifying the object")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.objspec.event.v1~"
                    "x.test12._.order_event.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.objspec.event.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "payload": {
                                "type": "object",
                                "required": ["orderId", "amount"],
                                "properties": {
                                    "orderId": {"type": "string"},
                                    "amount": {
                                        "type": "number",
                                        "minimum": 0
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
        Step(
            RunRequest("validate derived schema specifying object")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.objspec.event.v1~"
                    "x.test12._.order_event.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_3Level_L2SpecifiesObject(HttpRunner):
    """OP#12 - 3-level: base has object, L2 specifies it, L3 tightens"""
    config = Config(
        "OP#12 - 3-Level L2 Specifies Object"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with object property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.obj3a.resource.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["resourceId", "metadata"],
                "properties": {
                    "resourceId": {"type": "string", "format": "uuid"},
                    "metadata": {"type": "object"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register L2 schema specifying the object")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.obj3a.resource.v1~"
                    "x.test12._.file.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.obj3a.resource.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "metadata": {
                                "type": "object",
                                "required": ["fileName", "size"],
                                "properties": {
                                    "fileName": {
                                        "type": "string",
                                        "maxLength": 255
                                    },
                                    "size": {
                                        "type": "integer",
                                        "minimum": 0
                                    },
                                    "mimeType": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate L2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.obj3a.resource.v1~"
                    "x.test12._.file.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register L3 schema tightening the object")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.obj3a.resource.v1~"
                    "x.test12._.file.v1~x.test12._.image.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.obj3a.resource.v1~"
                            "x.test12._.file.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "fileName": {
                                        "type": "string",
                                        "maxLength": 128
                                    },
                                    "mimeType": {
                                        "type": "string",
                                        "enum": [
                                            "image/png",
                                            "image/jpeg",
                                            "image/webp"
                                        ]
                                    },
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"}
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate L3 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.obj3a.resource.v1~"
                    "x.test12._.file.v1~x.test12._.image.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_3Level_L2CompositionL3NestedObject(
    HttpRunner
):
    """OP#12 - 3-level: L2 specifies object as composition,
    L3 specifies nested
    """
    config = Config(
        "OP#12 - 3-Level L2 Composition L3 Nested Object"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with object property")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.obj3b.config.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["configId", "settings"],
                "properties": {
                    "configId": {"type": "string"},
                    "settings": {"type": "object"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register L2 specifying settings as composition")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.obj3b.config.v1~"
                    "x.test12._.app_config.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.obj3b.config.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "settings": {
                                "type": "object",
                                "required": ["theme", "notifications"],
                                "properties": {
                                    "theme": {
                                        "type": "string",
                                        "enum": [
                                            "light", "dark", "system"
                                        ]
                                    },
                                    "language": {
                                        "type": "string",
                                        "maxLength": 10
                                    },
                                    "notifications": {
                                        "type": "object"
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
        Step(
            RunRequest("validate L2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.obj3b.config.v1~"
                    "x.test12._.app_config.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register L3 specifying the nested object")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.obj3b.config.v1~"
                    "x.test12._.app_config.v1~"
                    "x.test12._.mobile_config.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.obj3b.config.v1~"
                            "x.test12._.app_config.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "settings": {
                                "type": "object",
                                "properties": {
                                    "theme": {
                                        "type": "string",
                                        "enum": ["light", "dark"]
                                    },
                                    "notifications": {
                                        "type": "object",
                                        "required": [
                                            "pushEnabled",
                                            "frequency"
                                        ],
                                        "properties": {
                                            "pushEnabled": {
                                                "type": "boolean"
                                            },
                                            "frequency": {
                                                "type": "string",
                                                "enum": [
                                                    "realtime",
                                                    "hourly",
                                                    "daily"
                                                ]
                                            },
                                            "quietHours": {
                                                "type": "object",
                                                "properties": {
                                                    "start": {
                                                        "type": "string",
                                                        "format": "time"
                                                    },
                                                    "end": {
                                                        "type": "string",
                                                        "format": "time"
                                                    }
                                                }
                                            }
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
        Step(
            RunRequest("validate L3 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.obj3b.config.v1~"
                    "x.test12._.app_config.v1~"
                    "x.test12._.mobile_config.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_3LevelHierarchy_Valid(HttpRunner):
    """OP#12 - Schema vs Schema: 3-level hierarchy with valid constraints"""
    config = Config("OP#12 - 3-Level Valid Hierarchy").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema level 1")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.hierarchy.entity.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["entityId", "type"],
                "properties": {
                    "entityId": {"type": "string", "format": "uuid"},
                    "type": {"type": "string"},
                    "description": {"type": "string", "maxLength": 500}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register level 2 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.hierarchy.entity.v1~"
                    "x.test12._.document.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.hierarchy.entity.v1~"},
                    {
                        "type": "object",
                        "required": ["title"],
                        "properties": {
                            "title": {"type": "string", "maxLength": 200},
                            "content": {"type": "string"},
                            "description": {
                                "type": "string",
                                "maxLength": 300
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.hierarchy.entity.v1~"
                    "x.test12._.document.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register level 3 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.hierarchy.entity.v1~"
                    "x.test12._.document.v1~x.test12._.article.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.hierarchy.entity.v1~"
                            "x.test12._.document.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "required": ["author", "publishedAt"],
                        "properties": {
                            "author": {"type": "string"},
                            "publishedAt": {
                                "type": "string",
                                "format": "date-time"
                            },
                            "title": {"type": "string", "maxLength": 150},
                            "description": {
                                "type": "string",
                                "maxLength": 200
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 3 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.hierarchy.entity.v1~"
                    "x.test12._.document.v1~x.test12._.article.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_3LevelHierarchy_L3ViolatesL2(
    HttpRunner
):
    """OP#12 - Schema vs Schema: 3-level where L3 violates L2"""
    config = Config("OP#12 - 3-Level L3 Violates L2").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema level 1")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.hier2.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                    "size": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 1000
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register level 2 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.hier2.base.v1~"
                    "x.test12._.medium.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.hier2.base.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "size": {
                                "type": "integer",
                                "minimum": 100,
                                "maximum": 500
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.hier2.base.v1~x.test12._.medium.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register level 3 schema violating level 2")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.hier2.base.v1~"
                    "x.test12._.medium.v1~x.test12._.bad_large.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.hier2.base.v1~"
                            "x.test12._.medium.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "size": {
                                "type": "integer",
                                "minimum": 100,
                                "maximum": 800
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 3 schema should fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.hier2.base.v1~"
                    "x.test12._.medium.v1~x.test12._.bad_large.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12SchemaValidation_3LevelHierarchy_L3ViolatesL1(
    HttpRunner
):
    """OP#12 - Schema vs Schema: 3-level where L3 violates L1"""
    config = Config("OP#12 - 3-Level L3 Violates L1").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema level 1")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.hier3.root.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["rootId", "status"],
                "properties": {
                    "rootId": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"]
                    },
                    "capacity": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 1000
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register level 2 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.hier3.root.v1~"
                    "x.test12._.branch.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.hier3.root.v1~"},
                    {
                        "type": "object",
                        "required": ["branchName"],
                        "properties": {
                            "branchName": {"type": "string"},
                            "capacity": {
                                "type": "integer",
                                "minimum": 100,
                                "maximum": 800
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.hier3.root.v1~x.test12._.branch.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register level 3 schema violating level 1")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.hier3.root.v1~"
                    "x.test12._.branch.v1~x.test12._.bad_leaf.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.hier3.root.v1~"
                            "x.test12._.branch.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": [
                                    "active",
                                    "inactive",
                                    "pending",
                                    "archived"
                                ]
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 3 schema should fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.hier3.root.v1~"
                    "x.test12._.branch.v1~x.test12._.bad_leaf.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12SchemaValidation_3LevelHierarchy_ConstraintCascade(
    HttpRunner
):
    """OP#12 - Schema vs Schema: 3-level progressive constraint tightening"""
    config = Config("OP#12 - 3-Level Constraint Cascade").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with max 1024")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.cascade.message.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["msgId", "payload"],
                "properties": {
                    "msgId": {"type": "string"},
                    "payload": {"type": "string", "maxLength": 1024}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register level 2 schema with max 512")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.cascade.message.v1~"
                    "x.test12._.sms.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.cascade.message.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "payload": {
                                "type": "string",
                                "maxLength": 512
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.cascade.message.v1~x.test12._.sms.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register level 3 schema with max 256")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.cascade.message.v1~"
                    "x.test12._.sms.v1~x.test12._.short_sms.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.cascade.message.v1~"
                            "x.test12._.sms.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "payload": {
                                "type": "string",
                                "maxLength": 256
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 3 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.cascade.message.v1~"
                    "x.test12._.sms.v1~x.test12._.short_sms.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
    ]


class TestCaseTestOp12SchemaValidation_3LevelHierarchy_InvalidCascade(
    HttpRunner
):
    """OP#12 - Schema vs Schema: 3-level where L3 exceeds L1 limit"""
    config = Config("OP#12 - 3-Level Invalid Cascade").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with max 128")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.badcascade.field.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["fieldId"],
                "properties": {
                    "fieldId": {"type": "string"},
                    "data": {"type": "string", "maxLength": 128}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register level 2 schema with max 100")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.badcascade.field.v1~"
                    "x.test12._.medium.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test12.badcascade.field.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "data": {"type": "string", "maxLength": 100}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.badcascade.field.v1~"
                    "x.test12._.medium.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register level 3 schema with max 256")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.badcascade.field.v1~"
                    "x.test12._.medium.v1~x.test12._.bad_large.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.badcascade.field.v1~"
                            "x.test12._.medium.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "data": {"type": "string", "maxLength": 256}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 3 schema should fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.badcascade.field.v1~"
                    "x.test12._.medium.v1~x.test12._.bad_large.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("validate level 3 schema should fail")
            .post("/validate-entity")
            .with_json({
                "gts_id": (
                    "gts.x.test12.badcascade.field.v1~"
                    "x.test12._.medium.v1~x.test12._.bad_large.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12_StringConstConflict(HttpRunner):
    """OP#12 - L2 const "abc", L3 const "def" → must fail."""
    config = Config("OP#12 - String Const Conflict").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_const_steps(
        "strconst", "status", "string", "abc", "def", False)


class TestCaseTestOp12_NumericConstConflict(HttpRunner):
    """OP#12 - L2 const 42, L3 const 99 → must fail."""
    config = Config("OP#12 - Numeric Const Conflict").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_const_steps(
        "numconst", "value", "number", 42, 99, False)


class TestCaseTestOp12_TypeChangeIntNumberInt(HttpRunner):
    """OP#12 - 3-level: Base integer, L2 widens to number, L3 narrows
    back to integer. L3 must fail because it narrows the type that L2
    already widened (floats valid in L2 would be rejected by L3).
    """
    config = Config(
        "OP#12 - Type Change int/number/int"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with integer field")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.typechange.score.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["scoreId", "points"],
                "properties": {
                    "scoreId": {"type": "string"},
                    "points": {"type": "integer"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register L2 schema widening to number")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.typechange.score.v1~"
                    "x.test12._.float_score.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.typechange.score.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "points": {"type": "number"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate L2 schema should fail - widens type")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.typechange.score.v1~"
                    "x.test12._.float_score.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
        Step(
            RunRequest("register L3 schema narrowing back to integer")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.typechange.score.v1~"
                    "x.test12._.float_score.v1~"
                    "x.test12._.int_score.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.typechange.score.v1~"
                            "x.test12._.float_score.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "points": {"type": "integer"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate L3 schema should also fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.typechange.score.v1~"
                    "x.test12._.float_score.v1~"
                    "x.test12._.int_score.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12_EnumReWidening(HttpRunner):
    """OP#12 - L2 narrows enum [a,b], L3 re-widens [a,b,c] → fail."""
    config = Config("OP#12 - Enum Re-Widening").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "enumwide", "level", "string",
        base_constraint=["admin", "editor", "viewer"],
        l2_constraint=["admin", "editor"],
        l3_constraint=["admin", "editor", "viewer"],
        keyword="enum")


class TestCaseTestOp12_MinLengthLoosening(HttpRunner):
    """OP#12 - L2 tightens minLength 5, L3 loosens to 3 → fail."""
    config = Config("OP#12 - MinLength Loosening").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "minlen", "code", "string",
        base_constraint=1, l2_constraint=5, l3_constraint=3,
        keyword="minLength")


class TestCaseTestOp12_TypeChangeStringToInt(HttpRunner):
    """OP#12 - Base string, L2 changes to integer → must fail."""
    config = Config("OP#12 - Type Change string to integer").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.typebreak.record.v1~", {
            "type": "object",
            "required": ["recordId", "label"],
            "properties": {
                "recordId": {"type": "string"},
                "label": {"type": "string"},
            },
        }, "register base with string field"),
        _register_derived(
            ("gts://gts.x.test12.typebreak.record.v1~"
             "x.test12._.bad_record.v1~"),
            "gts://gts.x.test12.typebreak.record.v1~",
            {"type": "object", "properties": {
                "label": {"type": "integer"},
            }},
            "register L2 changing string to integer",
        ),
        _validate_schema(
            ("gts.x.test12.typebreak.record.v1~"
             "x.test12._.bad_record.v1~"),
            False, "validate L2 should fail",
        ),
    ]


class TestCaseTestOp12_BooleanConstConflict(HttpRunner):
    """OP#12 - L2 const true, L3 const false → must fail."""
    config = Config("OP#12 - Boolean Const Conflict").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_const_steps(
        "boolconst", "enabled", "boolean", True, False, False)


class TestCaseTestOp12_MaximumLoosening(HttpRunner):
    """OP#12 - L2 tightens maximum 500, L3 loosens to 800 → fail."""
    config = Config("OP#12 - Maximum Loosening").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "maxloose", "count", "integer",
        base_constraint=1000, l2_constraint=500, l3_constraint=800,
        keyword="maximum", extra_prop={"minimum": 0})


class TestCaseTestOp12_StringConstIdempotent(HttpRunner):
    """OP#12 - L2 const "abc", L3 restates "abc" → must pass."""
    config = Config("OP#12 - String Const Idempotent").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_const_steps(
        "stridemp", "status", "string", "abc", "abc", True)


class TestCaseTestOp12_NumericConstIdempotent(HttpRunner):
    """OP#12 - L2 const 42, L3 restates 42 → must pass."""
    config = Config("OP#12 - Numeric Const Idempotent").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_const_steps(
        "numidemp", "value", "number", 42, 42, True)


class TestCaseTestOp12_BooleanConstIdempotent(HttpRunner):
    """OP#12 - L2 const true, L3 restates true → must pass."""
    config = Config("OP#12 - Boolean Const Idempotent").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_const_steps(
        "boolidemp", "active", "boolean", True, True, True)


class TestCaseTestOp12_EnumIdenticalRestatement(HttpRunner):
    """OP#12 - L2 narrows enum [r,w], L3 restates [r,w] → pass."""
    config = Config("OP#12 - Enum Identical Restatement").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "enumsame", "access", "string",
        base_constraint=["read", "write", "admin"],
        l2_constraint=["read", "write"],
        l3_constraint=["read", "write"],
        keyword="enum", expect_l3_ok=True)


class TestCaseTestOp12_RequiredSubsetInOverlay(HttpRunner):
    """OP#12 - L2 overlay lists subset of required → must pass
    (allOf union preserves base required).
    """
    config = Config(
        "OP#12 - Required Subset In Overlay (allOf union)"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.reqsub.contact.v1~", {
            "type": "object",
            "required": ["contactId", "name", "email"],
            "properties": {
                "contactId": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            },
        }, "register base with required fields"),
        _register_derived(
            ("gts://gts.x.test12.reqsub.contact.v1~"
             "x.test12._.slim_contact.v1~"),
            "gts://gts.x.test12.reqsub.contact.v1~",
            {
                "type": "object",
                "required": ["contactId", "name"],
                "properties": {
                    "contactId": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register L2 with subset required",
        ),
        _validate_schema(
            ("gts.x.test12.reqsub.contact.v1~"
             "x.test12._.slim_contact.v1~"),
            True, "validate L2 should pass",
        ),
    ]


class TestCaseTestOp12_PatternConflict(HttpRunner):
    """OP#12 - Base pattern ^[a-z]+$, L2 pattern ^[0-9]+$ → fail."""
    config = Config("OP#12 - Pattern Conflict").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.pattern.code.v1~", {
            "type": "object",
            "required": ["codeId", "value"],
            "properties": {
                "codeId": {"type": "string"},
                "value": {"type": "string", "pattern": "^[a-z]+$"},
            },
        }, "register base with alpha pattern"),
        _register_derived(
            ("gts://gts.x.test12.pattern.code.v1~"
             "x.test12._.num_code.v1~"),
            "gts://gts.x.test12.pattern.code.v1~",
            {"type": "object", "properties": {
                "value": {"type": "string", "pattern": "^[0-9]+$"},
            }},
            "register L2 with numeric pattern",
        ),
        _validate_schema(
            "gts.x.test12.pattern.code.v1~x.test12._.num_code.v1~",
            False, "validate L2 should fail",
        ),
    ]


class TestCaseTestOp12_MinItemsLoosening(HttpRunner):
    """OP#12 - L2 tightens minItems 5, L3 loosens to 2 → fail."""
    config = Config("OP#12 - MinItems Loosening").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "minitems", "entries", "array",
        base_constraint=1, l2_constraint=5, l3_constraint=2,
        keyword="minItems", extra_prop={"items": {"type": "string"}})


class TestCaseTestOp12_MinimumLoosening(HttpRunner):
    """OP#12 - L2 tightens minimum 10, L3 loosens to 5 → fail."""
    config = Config("OP#12 - Minimum Loosening").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "minloose", "degrees", "integer",
        base_constraint=0, l2_constraint=10, l3_constraint=5,
        keyword="minimum")


class TestCaseTestOp12_MaxLengthIdempotent(HttpRunner):
    """OP#12 - L2 tightens maxLength 100, L3 restates 100 → pass."""
    config = Config("OP#12 - MaxLength Idempotent").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "mlidemp", "text", "string",
        base_constraint=200, l2_constraint=100, l3_constraint=100,
        keyword="maxLength", expect_l3_ok=True)


class TestCaseTestOp12_ArrayTypeChange(HttpRunner):
    """OP#12 - 3-level: Base has array of strings, L2 narrows items
    to maxLength 50, L3 changes item type to integer.
    L3 must fail because changing array item type breaks
    compatibility with both L2 and base.
    """
    config = Config(
        "OP#12 - Array Item Type Change"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema with string array")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test12.arrtype.tags.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["tagListId", "tags"],
                "properties": {
                    "tagListId": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register L2 schema tightening string items")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.arrtype.tags.v1~"
                    "x.test12._.short_tags.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.arrtype.tags.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "maxLength": 50
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate L2 schema")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.arrtype.tags.v1~"
                    "x.test12._.short_tags.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
        ),
        Step(
            RunRequest("register L3 schema changing items to integer")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test12.arrtype.tags.v1~"
                    "x.test12._.short_tags.v1~"
                    "x.test12._.bad_tags.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test12.arrtype.tags.v1~"
                            "x.test12._.short_tags.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "integer"
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate L3 schema should fail")
            .post("/validate-schema")
            .with_json({
                "schema_id": (
                    "gts.x.test12.arrtype.tags.v1~"
                    "x.test12._.short_tags.v1~"
                    "x.test12._.bad_tags.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseTestOp12_ConstraintDropMaxLength(HttpRunner):
    """OP#12 - Derived drops maxLength → must fail."""
    config = Config("OP#12 - Constraint Drop maxLength").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "ml", "code", "string", "maxLength", 100)


class TestCaseTestOp12_ConstraintDropMinimum(HttpRunner):
    """OP#12 - Derived drops minimum → must fail."""
    config = Config("OP#12 - Constraint Drop minimum").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "min", "score", "number", "minimum", 0)


class TestCaseTestOp12_ConstraintDropEnum(HttpRunner):
    """OP#12 - Derived drops enum → must fail."""
    config = Config("OP#12 - Constraint Drop enum").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "enum", "status", "string", "enum", ["a", "b", "c"])


class TestCaseTestOp12_ConstraintDropConst(HttpRunner):
    """OP#12 - Derived drops const → must fail."""
    config = Config("OP#12 - Constraint Drop const").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "const", "version", "string", "const", "fixed")


class TestCaseTestOp12_ConstraintDropPattern(HttpRunner):
    """OP#12 - Derived drops pattern → must fail."""
    config = Config("OP#12 - Constraint Drop pattern").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "pat", "slug", "string", "pattern", "^[a-z]+$")


class TestCaseTestOp12_ConstraintDropItems(HttpRunner):
    """OP#12 - Derived drops items constraint → must fail."""
    config = Config("OP#12 - Constraint Drop items").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "items", "tags", "array", "items",
        {"type": "string", "maxLength": 50})


class TestCaseTestOp12_ConstraintDropMaximum(HttpRunner):
    """OP#12 - Derived drops maximum → must fail."""
    config = Config("OP#12 - Constraint Drop maximum").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "max", "amount", "number", "maximum", 1000)


class TestCaseTestOp12_ConstraintDropMinLength(HttpRunner):
    """OP#12 - Derived drops minLength → must fail."""
    config = Config("OP#12 - Constraint Drop minLength").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "minl", "name", "string", "minLength", 5)


class TestCaseTestOp12_ConstraintDropMinItems(HttpRunner):
    """OP#12 - Derived drops minItems → must fail."""
    config = Config("OP#12 - Constraint Drop minItems").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_2level_constraint_drop_steps(
        "mni", "items", "array", "minItems", 1,
        extra_base={"items": {"type": "string"}})


class TestCaseTestOp12_AdditionalPropertiesLoosened(HttpRunner):
    """OP#12 - Base AP false, derived sets AP true → must fail."""
    config = Config("OP#12 - additionalProperties Loosened").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.ap.loose.v1~", {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string"}},
            "additionalProperties": False,
        }, "register closed base schema"),
        _register_derived(
            "gts://gts.x.test12.ap.loose.v1~x.test12._.opened.v1~",
            "gts://gts.x.test12.ap.loose.v1~",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "additionalProperties": True,
            },
            "register derived setting AP true",
        ),
        _validate_schema(
            "gts.x.test12.ap.loose.v1~x.test12._.opened.v1~",
            False, "validate should fail - AP loosened",
        ),
    ]


class TestCaseTestOp12_AdditionalPropertiesOmitted(HttpRunner):
    """OP#12 - Base AP false, derived omits AP → must fail."""
    config = Config("OP#12 - additionalProperties Omitted").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.ap.omit.v1~", {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string"}},
            "additionalProperties": False,
        }, "register closed base schema"),
        _register_derived(
            "gts://gts.x.test12.ap.omit.v1~x.test12._.no_ap.v1~",
            "gts://gts.x.test12.ap.omit.v1~",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            },
            "register derived omitting AP",
        ),
        _validate_schema(
            "gts.x.test12.ap.omit.v1~x.test12._.no_ap.v1~",
            False, "validate should fail - AP omitted",
        ),
    ]


class TestCaseTestOp12_RequiredDroppedViaEmptyRequired(HttpRunner):
    """OP#12 - Derived has required:[] in overlay → must pass
    (allOf union preserves base required).
    """
    config = Config("OP#12 - Required Dropped Via Empty List").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.req.drop.v1~", {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
            },
        }, "register base with required fields"),
        _register_derived(
            "gts://gts.x.test12.req.drop.v1~x.test12._.empty_req.v1~",
            "gts://gts.x.test12.req.drop.v1~",
            {
                "type": "object",
                "required": [],
                "properties": {"extra": {"type": "string"}},
            },
            "register derived with empty required",
        ),
        _validate_schema(
            "gts.x.test12.req.drop.v1~x.test12._.empty_req.v1~",
            True, "validate should pass - empty overlay is ok",
        ),
    ]


class TestCaseTestOp12_RequiredFieldRemoval(HttpRunner):
    """OP#12 - Derived lists subset of required in overlay → must
    pass (allOf union keeps all base required).
    """
    config = Config("OP#12 - Required Field Removal").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.req.rm.v1~", {
            "type": "object",
            "required": ["id", "name", "email"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            },
        }, "register base schema"),
        _register_derived(
            "gts://gts.x.test12.req.rm.v1~x.test12._.less_req.v1~",
            "gts://gts.x.test12.req.rm.v1~",
            {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
            "register derived removing required email",
        ),
        _validate_schema(
            "gts.x.test12.req.rm.v1~x.test12._.less_req.v1~",
            True, "validate should pass - allOf union keeps all",
        ),
    ]


class TestCaseTestOp12_AllOfIntersectionNotOverride(HttpRunner):
    """OP#12 - 3-level: L2 maxLength 100, L3 overlay maxLength 150.
    L3 must fail because overlay loosens L2's constraint.
    """
    config = Config("OP#12 - allOf Intersection Not Override").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = _make_3level_loosening_steps(
        "allof_inter", "desc", "string",
        base_constraint=200, l2_constraint=100, l3_constraint=150,
        keyword="maxLength",
    )


class TestCaseTestOp12_EnumValueReplacement(HttpRunner):
    """OP#12 - 2-level: Base enum [a,b], derived changes to [a,d].
    Must fail because 'd' is not in the base enum and 'b' is removed.
    """
    config = Config("OP#12 - Enum Value Replacement").base_url(
        get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.enumrepl.item.v1~", {
            "type": "object",
            "required": ["itemId", "category"],
            "properties": {
                "itemId": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["a", "b"],
                },
            },
        }, "register base with enum [a, b]"),
        _register_derived(
            ("gts://gts.x.test12.enumrepl.item.v1~"
             "x.test12._.replaced.v1~"),
            "gts://gts.x.test12.enumrepl.item.v1~",
            {"type": "object", "properties": {
                "category": {
                    "type": "string",
                    "enum": ["a", "d"],
                },
            }},
            "register derived with enum [a, d]",
        ),
        _validate_schema(
            ("gts.x.test12.enumrepl.item.v1~"
             "x.test12._.replaced.v1~"),
            False,
            "validate should fail - enum value replaced",
        ),
    ]


class TestCaseTestOp12_RequiredPropertyGainsNullability(HttpRunner):
    """OP#12 - 2-level: Base has required string property, derived
    widens its type to ["string", "null"]. Must fail because a
    required property that was non-nullable in the base cannot
    become nullable in the derived schema.
    """
    config = Config(
        "OP#12 - Required Property Gains Nullability"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.nullable.rec.v1~", {
            "type": "object",
            "required": ["recId", "name"],
            "properties": {
                "recId": {"type": "string"},
                "name": {"type": "string"},
            },
        }, "register base with required non-nullable name"),
        _register_derived(
            ("gts://gts.x.test12.nullable.rec.v1~"
             "x.test12._.null_name.v1~"),
            "gts://gts.x.test12.nullable.rec.v1~",
            {"type": "object", "properties": {
                "name": {"type": ["string", "null"]},
            }},
            "register derived allowing null for name",
        ),
        _validate_schema(
            ("gts.x.test12.nullable.rec.v1~"
             "x.test12._.null_name.v1~"),
            False,
            "validate should fail - nullability added",
        ),
    ]


class TestCaseTestOp12_PrimitiveTypeWidening(HttpRunner):
    """OP#12 - 2-level: Base has "type": "string", derived widens
    to "type": ["string", "number"]. Must fail because the derived
    schema accepts values (numbers) that the base would reject.
    """
    config = Config(
        "OP#12 - Primitive Type Widening"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.typewiden.field.v1~", {
            "type": "object",
            "required": ["fieldId", "value"],
            "properties": {
                "fieldId": {"type": "string"},
                "value": {"type": "string"},
            },
        }, "register base with string-only value"),
        _register_derived(
            ("gts://gts.x.test12.typewiden.field.v1~"
             "x.test12._.wider.v1~"),
            "gts://gts.x.test12.typewiden.field.v1~",
            {"type": "object", "properties": {
                "value": {"type": ["string", "number"]},
            }},
            "register derived widening to [string, number]",
        ),
        _validate_schema(
            ("gts.x.test12.typewiden.field.v1~"
             "x.test12._.wider.v1~"),
            False,
            "validate should fail - type widened",
        ),
    ]


class TestCaseTestOp12_ConstViolatesMinimum(HttpRunner):
    """OP#12 - 2-level: Base has integer with minimum 42, derived
    sets const 32. Must fail because const 32 < minimum 42 — the
    derived const value violates the base constraint.
    """
    config = Config(
        "OP#12 - Const Violates Minimum"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register("gts://gts.x.test12.constmin.val.v1~", {
            "type": "object",
            "required": ["valId", "score"],
            "properties": {
                "valId": {"type": "string"},
                "score": {
                    "type": "integer",
                    "minimum": 42,
                },
            },
        }, "register base with minimum 42"),
        _register_derived(
            ("gts://gts.x.test12.constmin.val.v1~"
             "x.test12._.bad_const.v1~"),
            "gts://gts.x.test12.constmin.val.v1~",
            {"type": "object", "properties": {
                "score": {
                    "type": "integer",
                    "const": 32,
                },
            }},
            "register derived with const 32",
        ),
        _validate_schema(
            ("gts.x.test12.constmin.val.v1~"
             "x.test12._.bad_const.v1~"),
            False,
            "validate should fail - const 32 < minimum 42",
        ),
    ]


class TestCaseValidateEntity_ValidInstance(HttpRunner):
    """Validate Entity: Valid instance through unified endpoint"""
    config = Config("Validate Entity - Valid Instance").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testentity.events.type.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "type", "occurredAt"],
                "properties": {
                    "type": {"type": "string"},
                    "id": {"type": "string", "format": "uuid"},
                    "occurredAt": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "payload": {"type": "object"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.testentity.events.type.v1~"
                    "x.testentity.events.user_created.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testentity.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.testentity.events.type.v1~"
                                    "x.testentity.events.user_created.v1~"
                                )
                            },
                            "payload": {
                                "type": "object",
                                "required": ["userId", "email"],
                                "properties": {
                                    "userId": {
                                        "type": "string",
                                        "format": "uuid"
                                    },
                                    "email": {
                                        "type": "string",
                                        "format": "email"
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
        Step(
            RunRequest("register valid instance")
            .post("/entities")
            .with_json({
                "type": (
                    "gts.x.testentity.events.type.v1~"
                    "x.testentity.events.user_created.v1~"
                ),
                "id": (
                    "gts.x.testentity.events.type.v1~"
                    "x.testentity.events.user_created.v1~"
                    "x.testentity._.event1.v1"
                ),
                "occurredAt": "2025-09-20T18:35:00Z",
                "payload": {
                    "userId": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com"
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate instance via unified endpoint")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity.events.type.v1~"
                    "x.testentity.events.user_created.v1~"
                    "x.testentity._.event1.v1"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.entity_type", "instance")
        ),
    ]


class TestCaseValidateEntity_InvalidInstance(HttpRunner):
    """Validate Entity: Invalid instance through unified endpoint"""
    config = Config("Validate Entity - Invalid Instance").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testentity2.data.record.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["recordId", "value"],
                "properties": {
                    "recordId": {"type": "string"},
                    "value": {"type": "number", "minimum": 0}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register invalid instance missing required field")
            .post("/entities")
            .with_json({
                "type": "gts.x.testentity2.data.record.v1~",
                "id": (
                    "gts.x.testentity2.data.record.v1~"
                    "x.testentity2._.record1.v1"
                ),
                "recordId": "REC-001"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate invalid instance should fail")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity2.data.record.v1~"
                    "x.testentity2._.record1.v1"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.entity_type", "instance")
        ),
    ]


class TestCaseValidateEntity_ValidSchema(HttpRunner):
    """Validate Entity: Valid derived schema through unified endpoint"""
    config = Config("Validate Entity - Valid Schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testentity3.core.entity.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["entityId"],
                "properties": {
                    "entityId": {"type": "string", "format": "uuid"},
                    "description": {"type": "string", "maxLength": 200}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register valid derived schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.testentity3.core.entity.v1~"
                    "x.testentity3._.document.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testentity3.core.entity.v1~"},
                    {
                        "type": "object",
                        "required": ["title"],
                        "properties": {
                            "title": {"type": "string", "maxLength": 100},
                            "description": {
                                "type": "string",
                                "maxLength": 150
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate schema via unified endpoint")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity3.core.entity.v1~"
                    "x.testentity3._.document.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.entity_type", "schema")
        ),
    ]


class TestCaseValidateEntity_InvalidSchema(HttpRunner):
    """Validate Entity: Invalid derived schema through unified endpoint"""
    config = Config("Validate Entity - Invalid Schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testentity4.base.item.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["itemId"],
                "properties": {
                    "itemId": {"type": "string"},
                    "size": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    }
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register invalid derived schema loosening constraints")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.testentity4.base.item.v1~"
                    "x.testentity4._.bad_item.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testentity4.base.item.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "size": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 200
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate schema should fail")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity4.base.item.v1~"
                    "x.testentity4._.bad_item.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
            .assert_equal("body.entity_type", "schema")
        ),
    ]


class TestCaseValidateEntity_3LevelSchemaHierarchy(HttpRunner):
    """Validate Entity: 3-level schema hierarchy validation"""
    config = Config("Validate Entity - 3-Level Schema").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register level 1 base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testentity5.base.message.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["msgId"],
                "properties": {
                    "msgId": {"type": "string"},
                    "content": {"type": "string", "maxLength": 1000}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register level 2 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.testentity5.base.message.v1~"
                    "x.testentity5._.email.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testentity5.base.message.v1~"},
                    {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "maxLength": 500}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 2 schema")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity5.base.message.v1~"
                    "x.testentity5._.email.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.entity_type", "schema")
        ),
        Step(
            RunRequest("register level 3 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.testentity5.base.message.v1~"
                    "x.testentity5._.email.v1~x.testentity5._.notification.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.testentity5.base.message.v1~"
                            "x.testentity5._.email.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "maxLength": 200}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate level 3 schema")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity5.base.message.v1~"
                    "x.testentity5._.email.v1~x.testentity5._.notification.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.entity_type", "schema")
        ),
    ]


class TestCaseValidateEntity_MixedInstanceAndSchema(HttpRunner):
    """Validate Entity: Test both instance and schema in same test"""
    config = Config(
        "Validate Entity - Mixed Instance and Schema"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testentity6.product.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["productId", "name"],
                "properties": {
                    "productId": {"type": "string"},
                    "name": {"type": "string"},
                    "price": {"type": "number", "minimum": 0}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.testentity6.product.base.v1~"
                    "x.testentity6._.digital.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testentity6.product.base.v1~"},
                    {
                        "type": "object",
                        "required": ["downloadUrl"],
                        "properties": {
                            "downloadUrl": {
                                "type": "string",
                                "format": "uri"
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate derived schema")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity6.product.base.v1~"
                    "x.testentity6._.digital.v1~"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.entity_type", "schema")
        ),
        Step(
            RunRequest("register instance of derived schema")
            .post("/entities")
            .with_json({
                "type": (
                    "gts.x.testentity6.product.base.v1~"
                    "x.testentity6._.digital.v1~"
                ),
                "id": (
                    "gts.x.testentity6.product.base.v1~"
                    "x.testentity6._.digital.v1~x.testentity6._.prod1.v1"
                ),
                "productId": "PROD-001",
                "name": "eBook",
                "price": 9.99,
                "downloadUrl": "https://example.com/download/ebook"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("validate instance")
            .post("/validate-entity")
            .with_json({
                "entity_id": (
                    "gts.x.testentity6.product.base.v1~"
                    "x.testentity6._.digital.v1~x.testentity6._.prod1.v1"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.entity_type", "instance")
        ),
    ]


class TestCaseValidateEntity_NotFound(HttpRunner):
    """Validate Entity: Non-existent entity"""
    config = Config("Validate Entity - Not Found").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("validate non-existent entity")
            .post("/validate-entity")
            .with_json({
                "entity_id": "gts.x.nonexistent.entity.type.v1~"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", False)
        ),
    ]


class TestCaseValidateEntity_BaseSchemaNoParent(HttpRunner):
    """Validate Entity: Base schema with no parent (always valid)"""
    config = Config(
        "Validate Entity - Base Schema No Parent"
    ).base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register base schema without parent")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.testentity7.standalone.schema.v1~",
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
        Step(
            RunRequest("validate base schema should succeed")
            .post("/validate-entity")
            .with_json({
                "entity_id": "gts.x.testentity7.standalone.schema.v1~"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.ok", True)
            .assert_equal("body.entity_type", "schema")
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp12SchemaValidation_DerivedSchemaFullyMatches().test_start()
