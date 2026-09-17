#!/usr/bin/env python3
"""Generate reusable GTS examples by recording the HTTP traffic from this test suite.

The script runs the test files against a GTS server, collects registered entities, and
writes each entity after the server reports it valid or invalid. Invalid JSONC files
include the server's validation error as comments for use in fixtures and tooling.
"""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pytest
import requests

try:  # package import (pytest: tests.generate_examples)
    from .helpers.http_client import get_session
except ImportError:  # script import (python tests/generate_examples.py)
    from helpers.http_client import get_session


class EntityRecorder:
    def __init__(self):
        self.entities = {}
        self.results = {}
        self.entity_urls = {}
        # Explicit per-entity validation state: "unknown" | "valid" | "invalid".
        # A registered entity starts "unknown" and is promoted to valid/invalid
        # the first time a validation verdict for it is seen (during the tests
        # or in the explicit end-of-run pass).
        self.status = {}
        self._original_request = None

    def pytest_configure(self, config):
        self._original_request = requests.Session.request

        def record_request(session, method, url, **kwargs):
            return self._record_request(session, method, url, **kwargs)

        requests.Session.request = record_request

    def pytest_unconfigure(self, config):
        if self._original_request is not None:
            requests.Session.request = self._original_request

    def _record_request(self, session, method, url, **kwargs):
        response = self._original_request(session, method, url, **kwargs)
        if method.upper() != "POST":
            return response

        body = parse_json_body(kwargs)
        if body is None:
            return response

        path = urlparse(url).path.rstrip("/")
        if path == "/entities":
            self._record_entity(body, url, response)
        elif path in {
            "/validate-instance",
            "/validate-type-schema",
            "/validate-entity",
        }:
            self._record_validation(path, body, response)
        return response

    def _record_entity(self, body, url=None, response=None):
        entity_id, kind = identify_entity(body)
        if entity_id is None:
            return
        # A rejected registration did not change the server's stored entity, so
        # it must not change the recorder's corresponding body or validation state.
        if response is not None and not response.ok:
            return
        # An accepted POST /entities carries no validation verdict. Record the
        # submitted body and leave it unknown until explicit validation.
        self.entities[entity_id] = (kind, body)
        if url is not None:
            self.entity_urls[entity_id] = url
        self.status.setdefault(entity_id, "unknown")

    def validate_unvalidated_entities(self):
        """Explicitly validate every entity still in the "unknown" state.

        These were registered during the test run but never had a validation
        response observed for them, so their validity is unknown. Each is resolved
        through the unified ``/validate-entity`` endpoint so the SERVER decides
        whether the entity is a type-schema or an instance (via ``entity_type`` in
        the response). The recorder never infers schema-vs-instance from the JSON
        itself. The response promotes the entity to "valid"/"invalid" via
        ``_record_validation``.
        """
        unknown_ids = sorted(
            entity_id
            for entity_id, state in self.status.items()
            if state == "unknown" and entity_id in self.entity_urls
        )
        for entity_id in unknown_ids:
            body = {"entity_id": entity_id}
            response = get_session().post(
                urljoin(self.entity_urls[entity_id], "/validate-entity"),
                json=body,
                timeout=30,
            )
            self._record_validation("/validate-entity", body, response)

    def print_summary(self):
        """Print each entity's final valid/invalid/unknown state for reference."""
        print("\n=== Entity validation summary ===")
        for entity_id in sorted(self.status, key=lambda eid: (self.entities[eid][0], eid)):
            kind, _ = self.entities[entity_id]
            state = self.status[entity_id]
            print(f"  [{state.upper():>7}] {kind:<9} {entity_id}")

        counts = {"valid": 0, "invalid": 0, "unknown": 0}
        for state in self.status.values():
            counts[state] = counts.get(state, 0) + 1
        print(
            f"  -> {counts['valid']} valid, {counts['invalid']} invalid, "
            f"{counts['unknown']} unknown"
        )

    def _record_validation(self, path, body, response):
        result = parse_response(response)
        if not isinstance(result, dict) or not isinstance(result.get("ok"), bool):
            return

        field = (
            "type_id"
            if path == "/validate-type-schema"
            else "instance_id" if path == "/validate-instance" else "entity_id"
        )
        entity_id = normalize_id(body.get(field) or body.get("gts_id"))
        if entity_id is None:
            return

        entity = self.entities.get(entity_id)
        if entity is None:
            return

        # Classification is authoritative from the endpoint/response, never from
        # the recorder's own inspection of the JSON:
        #   - /validate-type-schema -> type-schema
        #   - /validate-instance    -> instance
        #   - /validate-entity      -> server-reported entity_type
        if path == "/validate-type-schema":
            kind = "types"
        elif path == "/validate-instance":
            kind = "instances"
        else:
            entity_type = result.get("entity_type")
            kind = (
                "types"
                if entity_type == "schema"
                else "instances" if entity_type == "instance" else entity[0]
            )
        self.results[(result["ok"], kind, entity_id)] = (
            entity[1],
            validation_error(result) if not result["ok"] else None,
        )
        # Promote the entity out of the "unknown" state now that a verdict exists.
        self.status[entity_id] = "valid" if result["ok"] else "invalid"


def parse_json_body(kwargs):
    if "json" in kwargs and isinstance(kwargs["json"], dict):
        return kwargs["json"]
    body = kwargs.get("data")
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    if not isinstance(body, str):
        return None
    try:
        value = json.loads(body)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def parse_response(response):
    try:
        return response.json()
    except (ValueError, requests.RequestException):
        return None


def normalize_id(value):
    if not isinstance(value, str) or not value:
        return None
    return value.removeprefix("gts://")


def identify_entity(body):
    schema_id = body.get("$id")
    if not isinstance(schema_id, str):
        schema_id = body.get("$$id")
    if isinstance(schema_id, str):
        return normalize_id(schema_id), "types"
    return normalize_id(body.get("id")), "instances"


def validation_error(result):
    error = result.get("error")
    if isinstance(error, str) and error:
        return re.sub(
            r"(file:///)(?:[^/'\"\s#]+/)+([^/'\"\s]+)", r"\1\2", error
        )
    if "errors" in result:
        return json.dumps(result["errors"], ensure_ascii=False)
    return "Validation response reported ok: false."


def output_filename(entity_id, kind, valid):
    suffix = ".schema.json" if kind == "types" else ".json"
    if not valid:
        suffix += "c"
    return f"{entity_id.replace('/', '_')}{suffix}"


def jsonc_content(body, error):
    comment = "\n".join(f"// Invalid: {line}" for line in error.splitlines())
    return f"{comment}\n{json.dumps(body, indent=2, ensure_ascii=False)}\n"


def write_examples(output_dir, results):
    written = 0
    for (valid, kind, entity_id), (body, error) in sorted(results.items()):
        validity = "valid" if valid else "invalid"
        destination = (
            output_dir / validity / kind / output_filename(entity_id, kind, valid)
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = (
            json.dumps(body, indent=2, ensure_ascii=False) + "\n"
            if valid
            else jsonc_content(body, error)
        )
        destination.write_text(content, encoding="utf-8")
        written += 1
    return written


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate GTS examples from test HTTP traffic."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("gts-test-examples"),
        help="Directory for generated examples (default: gts-examples).",
    )
    parser.add_argument("--gts-base-url", help="GTS server URL, forwarded to pytest.")
    parser.add_argument(
        "test_files", nargs="*", type=Path, help="Optional test_* files to run."
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    tests_dir = Path(__file__).parent
    test_files = args.test_files or sorted(tests_dir.glob("test_*.py"))
    recorder = EntityRecorder()
    pytest_args = [str(path) for path in test_files]
    if args.gts_base_url:
        pytest_args.extend(["--gts-base-url", args.gts_base_url])
    exit_code = pytest.main(pytest_args, plugins=[recorder])
    recorder.validate_unvalidated_entities()
    written = write_examples(args.output, recorder.results)
    recorder.print_summary()
    print(f"Generated {written} examples in {args.output}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
