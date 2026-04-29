"""Shared test helpers for HttpRunner-based GTS tests.

Provides reusable Step builders for registering and validating schemas,
instances, and entities via the GTS HTTP API.
"""

from httprunner import Step, RunRequest


def register(gts_id, schema_body, label="register schema"):
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


def register_derived(gts_id, base_ref, overlay, label="register derived", top_level=None):
    """Register a derived schema that uses allOf with a $$ref.

    top_level: optional dict of extra keys to add at schema top level
    (e.g. {"x-gts-final": True}) — these MUST NOT go inside allOf.
    """
    body = {
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "allOf": [
            {"$$ref": base_ref},
            overlay,
        ],
    }
    if top_level:
        body.update(top_level)
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


def register_instance(instance_body, label="register instance"):
    """Register an instance via POST /entities."""
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(instance_body)
        .validate()
        .assert_equal("status_code", 200)
    )


def validate_type_schema(type_id, expect_ok, label="validate type schema"):
    """Validate a derived GTS Type Schema via POST /validate-type-schema."""
    step = (
        RunRequest(label)
        .post("/validate-type-schema")
        .with_json({"type_id": type_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    return Step(step)


def validate_entity(entity_id, expect_ok, label="validate entity", expected_entity_type=None):
    """Validate an entity via POST /validate-entity."""
    step = (
        RunRequest(label)
        .post("/validate-entity")
        .with_json({"entity_id": entity_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    if expected_entity_type is not None:
        step = step.assert_equal("body.entity_type", expected_entity_type)
    return Step(step)


def validate_instance(instance_id, expect_ok, label="validate instance", expected_id=None):
    """Validate an instance via POST /validate-instance."""
    step = (
        RunRequest(label)
        .post("/validate-instance")
        .with_json({"instance_id": instance_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    if expected_id is not None:
        step = step.assert_equal("body.id", expected_id)
    return Step(step)
