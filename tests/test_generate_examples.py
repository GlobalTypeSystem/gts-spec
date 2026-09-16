import types

import pytest

from .generate_examples import (
    EntityRecorder,
    identify_entity,
    validation_error,
    write_examples,
)

pytestmark = pytest.mark.unit


class Response:
    def __init__(self, body, ok=True):
        self.body = body
        self.ok = ok

    def json(self):
        return self.body


def test_identify_entity_normalizes_type_identifier():
    assert identify_entity({"$id": "gts://gts.x.demo._.thing.v1~"}) == (
        "gts.x.demo._.thing.v1~",
        "types",
    )


def test_validation_error_strips_absolute_file_url_path():
    result = {
        "error": "validation error: jsonschema validation failed with "
        "'file:///Users/User.Name/git/github/gts-go/gts.x.test6.formats.standard.v1~#'"
    }

    assert validation_error(result) == (
        "validation error: jsonschema validation failed with "
        "'file:///gts.x.test6.formats.standard.v1~#'"
    )


def test_recorder_classifies_entity_validation_results():
    recorder = EntityRecorder()
    type_id = "gts.x.demo._.thing.v1~"
    instance_id = f"{type_id}x.demo._.example.v1"
    type_body = {
        "$id": f"gts://{type_id}",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
    }
    instance_body = {"id": instance_id, "type": type_id, "value": "example"}

    recorder._record_entity(type_body)
    recorder._record_entity(instance_body)
    recorder._record_validation(
        "/validate-type-schema", {"type_id": type_id}, Response({"ok": True})
    )
    recorder._record_validation(
        "/validate-instance",
        {"instance_id": instance_id},
        Response({"ok": False, "error": "missing required value"}),
    )

    assert recorder.results == {
        (True, "types", type_id): (type_body, None),
        (False, "instances", instance_id): (instance_body, "missing required value"),
    }


def test_recorder_validates_registered_entities_missing_explicit_validation(monkeypatch):
    recorder = EntityRecorder()
    base_type_id = "gts.x.demo._.base.v1~"
    derived_type_id = f"{base_type_id}x.demo._.derived.v1~"
    instance_id = f"{base_type_id}x.demo._.example.v1"
    url = "http://gts.example/entities"
    response = Response({}, ok=True)

    recorder._record_entity({"$id": f"gts://{base_type_id}"}, url, response)
    recorder._record_entity({"$id": f"gts://{derived_type_id}"}, url, response)
    recorder._record_entity({"id": instance_id}, url, response)
    recorder._record_validation(
        "/validate-type-schema", {"type_id": derived_type_id}, Response({"ok": True})
    )
    calls = []

    # The unvalidated entities are resolved through the unified /validate-entity
    # endpoint; the server (mocked here) reports whether each is a schema or an
    # instance via `entity_type`, so the recorder never classifies the JSON.
    def post(request_url, **kwargs):
        calls.append((request_url, kwargs))
        entity_id = kwargs["json"]["entity_id"]
        entity_type = "schema" if entity_id.endswith("~") else "instance"
        return Response({"ok": True, "entity_type": entity_type})

    fake_session = types.SimpleNamespace(post=post)
    monkeypatch.setattr(
        "tests.generate_examples.get_session", lambda: fake_session
    )

    recorder.validate_unvalidated_entities()

    assert calls == [
        (
            "http://gts.example/validate-entity",
            {"json": {"entity_id": base_type_id}, "timeout": 30},
        ),
        (
            "http://gts.example/validate-entity",
            {"json": {"entity_id": instance_id}, "timeout": 30},
        ),
    ]
    assert recorder.results[(True, "types", base_type_id)] == (
        {"$id": f"gts://{base_type_id}"},
        None,
    )
    assert recorder.results[(True, "instances", instance_id)] == ({"id": instance_id}, None)


def test_registration_marks_entity_unknown_until_verdict():
    recorder = EntityRecorder()
    type_id = "gts.x.demo._.thing.v1~"
    url = "http://gts.example/entities"

    recorder._record_entity({"$id": f"gts://{type_id}"}, url, Response({}, ok=True))
    assert recorder.status == {type_id: "unknown"}

    recorder._record_validation(
        "/validate-type-schema", {"type_id": type_id}, Response({"ok": True})
    )
    assert recorder.status == {type_id: "valid"}


def test_unvalidated_entity_without_bool_verdict_stays_unknown(monkeypatch):
    recorder = EntityRecorder()
    type_id = "gts.x.demo._.mystery.v1~"
    url = "http://gts.example/entities"

    recorder._record_entity({"$id": f"gts://{type_id}"}, url, Response({}, ok=True))

    # Server responds without a boolean `ok`, so the verdict stays unknown.
    monkeypatch.setattr(
        "tests.generate_examples.get_session",
        lambda: types.SimpleNamespace(post=lambda *a, **k: Response({"pending": True})),
    )

    recorder.validate_unvalidated_entities()

    assert recorder.results == {}
    assert recorder.status == {type_id: "unknown"}


def test_write_examples_uses_validity_and_entity_kind_directories(tmp_path):
    results = {
        (True, "types", "gts.x.demo._.thing.v1~"): (
            {"$id": "gts://gts.x.demo._.thing.v1~"},
            None,
        ),
        (False, "instances", "gts.x.demo._.thing.v1~x.demo._.example.v1"): (
            {"id": "example"},
            "missing required value",
        ),
    }

    assert write_examples(tmp_path, results) == 2
    assert (tmp_path / "valid/types/gts.x.demo._.thing.v1~.schema.json").is_file()
    invalid_path = (
        tmp_path / "invalid/instances/gts.x.demo._.thing.v1~x.demo._.example.v1.jsonc"
    )
    assert (
        invalid_path.read_text()
        == '// Invalid: missing required value\n{\n  "id": "example"\n}\n'
    )
