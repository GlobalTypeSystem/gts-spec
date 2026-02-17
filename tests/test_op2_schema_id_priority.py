"""
OP#2 - Schema ID Priority Tests

These tests verify that chained GTS IDs ALWAYS take priority for schema_id
extraction over explicit `type` fields (or gtsTid, gtsType, etc.).

The chained GTS ID is the authoritative source for determining an instance's
parent schema. Any explicit type fields are ignored when the ID is chained.
"""

import requests
from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseOp2SchemaIdPriority_ChainTakesPrecedence(HttpRunner):
    """
    When a well-known instance has both:
    - A chained GTS ID in `id` (implying a parent type)
    - An explicit `type` field declaring a different parent type

    The chained GTS ID MUST take priority for schema_id.
    The explicit `type` field is ignored.
    """
    config = Config(
        "OP#2 - Schema ID Priority: chain takes precedence over type"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("chained ID schema overrides explicit type field")
            .post("/extract-id")
            .with_json({
                # Chained ID implies parent: gts.acme.core.models.user.v1~
                "id": (
                    "gts.acme.core.models.user.v1~"
                    "acme.core.instances.user1.v1"
                ),
                # Explicit type declares different parent (IGNORED)
                "type": "gts.acme.core.models.product.v1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                (
                    "gts.acme.core.models.user.v1~"
                    "acme.core.instances.user1.v1"
                ),
            )
            # The chained ID MUST take precedence, type field is ignored
            .assert_equal(
                "body.schema_id",
                "gts.acme.core.models.user.v1~",
            )
            .assert_equal("body.selected_entity_field", "id")
            .assert_equal("body.selected_schema_id_field", "id")
            .assert_equal("body.is_schema", False)
        ),
    ]


class TestCaseOp2SchemaIdPriority_ChainUsedAlone(HttpRunner):
    """
    When a well-known instance has only a chained GTS ID (no explicit
    `type` field), the schema_id MUST be derived from the chain.
    """
    config = Config(
        "OP#2 - Schema ID Priority: chain used alone"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("schema derived from chain when no explicit type")
            .post("/extract-id")
            .with_json({
                # Only chained ID, no explicit type field
                "id": (
                    "gts.acme.core.models.user.v1~"
                    "acme.core.instances.user1.v1"
                ),
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                (
                    "gts.acme.core.models.user.v1~"
                    "acme.core.instances.user1.v1"
                ),
            )
            # Schema derived from chain (first segment ending with ~)
            .assert_equal("body.schema_id", "gts.acme.core.models.user.v1~")
            .assert_equal("body.selected_entity_field", "id")
            .assert_equal("body.selected_schema_id_field", "id")
            .assert_equal("body.is_schema", False)
        ),
    ]


class TestCaseOp2SchemaIdPriority_TypeUsedForAnonymous(HttpRunner):
    """
    For anonymous instances (UUID id, not a GTS ID), the explicit `type`
    field is used to determine schema_id.
    """
    config = Config(
        "OP#2 - Schema ID Priority: type used for anonymous instances"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("type field used for anonymous instance")
            .post("/extract-id")
            .with_json({
                # Anonymous instance (UUID, not a GTS ID)
                "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
                # Explicit type is used since ID is not chained
                "type": "gts.acme.core.models.product.v1~",
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                "7a1d2f34-5678-49ab-9012-abcdef123456",
            )
            # Type field is used for anonymous instances
            .assert_equal("body.schema_id", "gts.acme.core.models.product.v1~")
            .assert_equal("body.selected_entity_field", "id")
            .assert_equal("body.selected_schema_id_field", "type")
            .assert_equal("body.is_schema", False)
        ),
    ]


def test_op2_chained_id_takes_priority_over_explicit_type() -> None:
    """
    When a well-known instance has both a chained GTS ID and an explicit
    `type` field, the chained GTS ID MUST take priority for schema_id.

    The explicit `type` field is ignored when a chained ID is present.
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        # Chained ID implies parent type: gts.acme.core.models.user.v1~
        "id": (
            "gts.acme.core.models.user.v1~"
            "acme.core.instances.user1.v1"
        ),
        # Explicit type declares different parent (should be IGNORED)
        "type": "gts.acme.core.models.product.v1~",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()

    # Instance ID should be preserved
    assert body["id"] == payload["id"]
    assert body["is_schema"] is False

    # The chained ID MUST take precedence over explicit type field
    assert body["schema_id"] == "gts.acme.core.models.user.v1~", (
        f"Expected schema_id from chained ID "
        f"('gts.acme.core.models.user.v1~'), "
        f"but got '{body.get('schema_id')}' (explicit type should be ignored)"
    )
    assert body["selected_schema_id_field"] == "id", (
        f"Expected selected_schema_id_field to be 'id', "
        f"but got '{body.get('selected_schema_id_field')}'"
    )


def test_op2_chain_derivation_alone() -> None:
    """
    When a well-known instance has only a chained GTS ID (no explicit
    `type`), the schema_id MUST be derived from the chain.
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        "id": (
            "gts.acme.core.models.user.v1~"
            "acme.core.instances.user1.v1"
        ),
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()

    assert body["id"] == payload["id"]
    assert body["is_schema"] is False
    assert body["schema_id"] == "gts.acme.core.models.user.v1~"
    assert body["selected_schema_id_field"] == "id"


def test_op2_type_used_for_anonymous_instance() -> None:
    """
    For anonymous instances (UUID id), the explicit `type` field is used
    since there is no chained GTS ID to derive schema from.
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
        "type": "gts.acme.core.models.order.v1~",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()

    assert body["id"] == payload["id"]
    assert body["is_schema"] is False
    # Type field is used for anonymous instances
    assert body["schema_id"] == "gts.acme.core.models.order.v1~"
    assert body["selected_schema_id_field"] == "type"


def test_op2_gtsTid_used_for_anonymous_instance() -> None:
    """
    The `gtsTid` field can also be used for anonymous instances when
    there is no chained GTS ID.
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
        "gtsTid": "gts.acme.core.models.order.v1~",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()

    assert body["id"] == payload["id"]
    assert body["is_schema"] is False
    # gtsTid field is used for anonymous instances
    assert body["schema_id"] == "gts.acme.core.models.order.v1~"
    assert body["selected_schema_id_field"] == "gtsTid"


def test_op2_deeply_chained_id_ignores_explicit_type() -> None:
    """
    For deeply chained IDs (3+ segments), the chain still takes priority
    and any explicit type field is ignored.
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        # 3-segment chained ID
        "id": (
            "gts.x.core.events.type.v1~"
            "x.core.audit.event.v1~"
            "x.marketplace.orders.purchase.v1"
        ),
        # Explicit type pointing elsewhere (IGNORED)
        "type": "gts.different.schema.type.v1~",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()

    assert body["id"] == payload["id"]
    assert body["is_schema"] is False
    # Chain takes priority, explicit type is ignored
    # Schema is derived from the chain (up to last ~)
    expected_schema = (
        "gts.x.core.events.type.v1~"
        "x.core.audit.event.v1~"
    )
    assert body["schema_id"] == expected_schema
    assert body["selected_schema_id_field"] == "id"


def test_op2_single_segment_gts_id_uses_explicit_type() -> None:
    """
    For single-segment GTS IDs (no chain), the explicit `type` field
    is used since there's no parent to derive from the ID.
    """
    url = get_gts_base_url() + "/extract-id"
    payload = {
        # Single-segment GTS ID (no chain, looks like a schema ID)
        "id": "gts.acme.core.models.user.v1.0",
        # Explicit type is used since ID has no chain
        "type": "gts.acme.core.models.base.v1~",
    }
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()

    assert body["id"] == payload["id"]
    assert body["is_schema"] is False
    # Type field is used for single-segment IDs (no chain to derive from)
    assert body["schema_id"] == "gts.acme.core.models.base.v1~"
    assert body["selected_schema_id_field"] == "type"
