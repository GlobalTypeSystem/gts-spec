import requests
from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseTestOp2IdExtraction_Case1(HttpRunner):
    config = Config("OP#2 - Extract ID (case 1)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("extract id (case 1)")
            .post("/extract-id")
            .with_json({
                "id": "gts.x.test2.api.endpoint.v0.1",
                "schema": "gts.x.test2.api.endpoint.v0~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "gts.x.test2.api.endpoint.v0.1")
            .assert_equal("body.schema_id", "gts.x.test2.api.endpoint.v0~")
            .assert_equal("body.selected_entity_field", "id")
            .assert_equal("body.selected_schema_id_field", "schema")
            .assert_equal("body.is_schema", False)
        ),
    ]


class TestCaseTestOp2IdExtraction_Case2(HttpRunner):
    config = Config("OP#2 - Extract ID (case 2)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("extract id (case 2)")
            .post("/extract-id")
            .with_json({
                "id": (
                    "gts.x.test2.events.type.v1~abc.app._."
                    "custom_event.v1.2"
                )
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                "gts.x.test2.events.type.v1~abc.app._.custom_event.v1.2",
            )
            .assert_equal("body.schema_id", "gts.x.test2.events.type.v1~")
            .assert_equal("body.selected_entity_field", "id")
            .assert_equal("body.selected_schema_id_field", "id")
            .assert_equal("body.is_schema", False)
        ),
    ]


class TestCaseTestOp2IdExtraction_Case3(HttpRunner):
    config = Config("OP#2 - Extract ID (case 3)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("extract id (case 3)")
            .post("/extract-id")
            .with_json({
                "id": "gts.x.core.events.topic.v1~x.commerce._.orders.v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                "gts.x.core.events.topic.v1~x.commerce._.orders.v1.0",
            )
            .assert_equal(
                "body.schema_id",
                "gts.x.core.events.topic.v1~",
            )
            .assert_equal("body.selected_entity_field", "id")
            .assert_equal("body.selected_schema_id_field", "id")
            .assert_equal("body.is_schema", False)
        ),
    ]


class TestCaseTestOp2IdExtraction_Case4(HttpRunner):
    config = Config("OP#2 - Extract ID (case 4)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("extract id (case 4)")
            .post("/extract-id")
            .with_json({
                "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
                "type": (
                    "gts.x.core.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.0~"
                ),
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                "7a1d2f34-5678-49ab-9012-abcdef123456",
            )
            .assert_equal(
                "body.schema_id",
                (
                    "gts.x.core.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.0~"
                ),
            )
            .assert_equal("body.selected_entity_field", "id")
            .assert_equal("body.selected_schema_id_field", "type")
            .assert_equal("body.is_schema", False)
        ),
    ]


class TestCaseTestOp2IdExtraction_Case5_GtsBaseSchema(HttpRunner):
    """
    Schemas MUST be detected by presence of $schema; GTS $id MUST be normalized
    by stripping gts://.
    """
    config = Config("OP#2 - Extract ID (case 5: GTS base schema)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("extract id for base schema")
            .post("/extract-id")
            .with_json({
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "$$id": "gts://gts.x.core.events.type.v1~",
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
            # NOTE:
            # - These two cases send JSON Schema keys ($schema / $id).
            # - HttpRunner/httprunner uses "$..." for variable/template syntax.
            #   so $-prefixed keys can get interpolated and be brittle here.
            # - Therefore this class is only a smoke test:
            #   we only check the server classifies the input as a schema.
            # - The real contract checks are implemented below
            #   (plain pytest + `requests`).
            .assert_equal("body.is_schema", True)
        ),
    ]


class TestCaseTestOp2IdExtraction_Case6_GtsDerivedSchema(HttpRunner):
    """
    For derived schemas, schema_id is derived from the $id chain
    (not taken from $schema).
    """
    config = Config("OP#2 - Extract ID (case 6: GTS derived schema)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("extract id for derived schema")
            .post("/extract-id")
            .with_json({
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "$$id": (
                    "gts://gts.x.core.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.0~"
                ),
                "type": "object",
            })
            .validate()
            .assert_equal("status_code", 200)
            # NOTE:
            # - These two cases send JSON Schema keys ($schema / $id).
            # - HttpRunner/httprunner uses "$..." for variable/template syntax.
            #   so $-prefixed keys can get interpolated and be brittle here.
            # - Therefore this class is only a smoke test:
            #   we only check the server classifies the input as a schema.
            # - The real contract checks are implemented below
            #   (plain pytest + `requests`).
            .assert_equal("body.is_schema", True)
        ),
    ]


def test_op2_extract_id_gts_base_schema_normalizes_id() -> None:
    """Schema detection uses $schema; gts:// prefix is stripped from $id."""
    url = get_gts_base_url() + "/extract-id"
    payload = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "gts://gts.x.core.events.type.v1~",
        "type": "object",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["is_schema"] is True
    assert body["id"] == "gts.x.core.events.type.v1~"
    assert body["schema_id"] == "http://json-schema.org/draft-07/schema#"


def test_op2_extract_id_gts_derived_schema_parent_from_chain() -> None:
    """For derived schemas, schema_id is derived from the $id chain."""
    url = get_gts_base_url() + "/extract-id"
    payload = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": (
            "gts://gts.x.core.events.type.v1~"
            "x.commerce.orders.order_placed.v1.0~"
        ),
        "type": "object",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["is_schema"] is True
    assert (
        body["id"]
        == "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~"
    )
    assert body["schema_id"] == "gts.x.core.events.type.v1~"


def test_op2_extract_id_schema_without_id_is_non_gts_schema() -> None:
    """
    If $schema is present but $id is missing, the document is a schema
    (Rule A) but it is NOT a GTS schema (Rule C #2).
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["is_schema"] is True
    # Not a GTS schema: no canonical gts.* id can be extracted.
    extracted_id = body.get("id")
    assert extracted_id in (None, "") or not str(extracted_id).startswith(
        "gts."
    )
    # Without a GTS $id chain, schema_id falls back to $schema.
    assert body.get("schema_id") == payload["$schema"]


def test_op2_extract_id_id_without_schema_is_not_a_gts_schema() -> None:
    """
    If $id is present but $schema is missing, the document is an instance
    (Rule A). The '$id' field value is a GTS identifier (not a GTS schema).
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
        "$id": "gts://gts.x.core.events.test_type.v10~",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["is_schema"] is False
    assert body["id"] == payload["$id"].replace("gts://", "")
    # No type field => schema_id should not be inferred from $id.
    assert body.get("schema_id") is None


def test_op2_extract_id_uuid_without_type_is_non_gts_instance() -> None:
    """
    UUID id without type/schema reference is a non-GTS instance (Rule C #3).
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {"id": "7a1d2f34-5678-49ab-9012-abcdef123456"}
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["is_schema"] is False
    assert body["id"] == payload["id"]
    assert body.get("schema_id") is None


def test_op2_extract_id_non_gts_id_is_non_gts_instance() -> None:
    """Non-GTS id value without type/schema reference is a non-GTS instance."""
    url = get_gts_base_url() + "/extract-id"
    payload = {"id": "not-a-gts-id"}
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["is_schema"] is False
    assert body["id"] == payload["id"]
    assert body.get("schema_id") is None
