"""Shared test helpers for HttpRunner-based GTS tests.

Provides reusable Step builders for registering and validating schemas,
instances, and entities via the GTS HTTP API.
"""

from httprunner import Config, HttpRunner, RunRequest, RunTestCase, Step

from ..conftest import get_gts_base_url


def register(gts_id, schema_body, label="register schema"):
    """Register a schema via POST /entities."""
    body = {
        **schema_body,
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
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

    The document-level GTS keywords x-gts-traits / x-gts-traits-schema MUST
    appear at the schema top level, not nested inside an allOf entry
    (GTS spec §9.12). If a caller places them in the `overlay`, they are
    transparently hoisted to the top level so existing trait tests express
    the spec-correct placement without restating every call site.
    """
    overlay = dict(overlay)
    trait_kws = ("x-gts-traits", "x-gts-traits-schema")
    hoisted = {kw: overlay.pop(kw) for kw in trait_kws if kw in overlay}
    if top_level:
        clobbered = [kw for kw in trait_kws if kw in top_level]
        if clobbered:
            raise ValueError(
                "top_level must not contain trait keywords "
                f"{clobbered}; pass them in `overlay` so they are hoisted"
            )
    body = {
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "allOf": [
            {"$$ref": base_ref},
            overlay,
        ],
    }
    body.update(hoisted)
    if top_level:
        body.update(top_level)
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


def register_derived_redeclared(
    gts_id, base_ref, body, label="register derived (no allOf)", top_level=None
):
    """Register a derived schema without allOf — caller restates parent fields directly.

    Per ADR-0001 (GTS as a JSON Schema extension, dialect-agnostic; not a formal
    JSON Schema Dialect), derivation is established by the chained $id alone;
    the body MAY use any syntactically valid JSON Schema form.
    `base_ref` is accepted for parity with register_derived() and documents intent.

    `body` is the entire schema body (caller is responsible for restating any
    parent fields that need to participate in OP#12 compatibility). The helper
    only injects $id and $schema; no allOf wrapping is added.
    top_level: optional dict merged into body at the top level.
    """
    full = {
        **body,
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
    }
    if top_level:
        full.update(top_level)
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(full)
        .validate()
        .assert_equal("status_code", 200)
    )


def register_abstract(gts_id, schema_body, label="register abstract"):
    """Register a schema marked x-gts-abstract: true.

    Per ADR-0003, abstract types skip the trait-completeness check at
    /validate-type-schema time.
    """
    body = {
        **schema_body,
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "x-gts-abstract": True,
    }
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


def validate_type_schema(
    type_id, expect_ok, label="validate type schema", gts_ref_validation=None
):
    """Validate a type schema through the specific and unified endpoints."""
    specific = RunRequest(f"{label} via validate-type-schema").post(
        "/validate-type-schema"
    )
    if gts_ref_validation is not None:
        specific = specific.with_params(**{"gts-ref-validation": gts_ref_validation})
    specific = (
        specific.with_json({"type_id": type_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    return _dual_validation_step(
        type_id, expect_ok, label, "schema", specific, gts_ref_validation
    )


def validate_entity(
    entity_id,
    expect_ok,
    label="validate entity",
    expected_entity_type=None,
    gts_ref_validation=None,
):
    """Validate an entity via POST /validate-entity."""
    request = RunRequest(label).post("/validate-entity")
    if gts_ref_validation is not None:
        request = request.with_params(**{"gts-ref-validation": gts_ref_validation})
    step = (
        request.with_json({"entity_id": entity_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    if expected_entity_type is not None:
        step = step.assert_equal("body.entity_type", expected_entity_type)
    return Step(step)


def validate_instance(
    instance_id,
    expect_ok,
    label="validate instance",
    expected_id=None,
    gts_ref_validation=None,
):
    """Validate an instance through the specific and unified endpoints."""
    specific = RunRequest(f"{label} via validate-instance").post(
        "/validate-instance"
    )
    if gts_ref_validation is not None:
        specific = specific.with_params(**{"gts-ref-validation": gts_ref_validation})
    specific = (
        specific.with_json({"instance_id": instance_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    if expected_id is not None:
        specific = specific.assert_equal("body.id", expected_id)
    return _dual_validation_step(
        instance_id, expect_ok, label, "instance", specific, gts_ref_validation
    )


def _dual_validation_step(
    entity_id, expect_ok, label, entity_type, specific, gts_ref_validation=None
):
    class DualValidation(HttpRunner):
        config = Config("dual endpoint validation").base_url(get_gts_base_url())
        teststeps = [
            Step(specific),
            validate_entity(
                entity_id,
                expect_ok,
                f"{label} via validate-entity",
                expected_entity_type=entity_type,
                gts_ref_validation=gts_ref_validation,
            ),
        ]

    return Step(RunTestCase(label).call(DualValidation))
