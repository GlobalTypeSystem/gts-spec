"""Shared, connection-pooled HTTP client for the GTS test suite.

Module-level ``requests.get`` / ``requests.post`` helpers create and discard a
fresh ``Session`` on every call, so each request pays a new TCP (and TLS)
handshake. Reusing a single ``requests.Session`` with a mounted ``HTTPAdapter``
enables keep-alive connection reuse across all the raw request call sites in the
suite (conftest probe, the OP#2 plain-function tests, and generate_examples).

Conformance tests assert exact server status codes, so the adapter is configured
with ``max_retries=0``: connections are pooled, but responses are never retried
or masked.

``GtsTestAPI`` wraps such a session for plain pytest tests (fixture ``gts_api``):
it registers entities under a per-test ID namespace and checks verdicts of the
validation endpoints. Schemas, payloads and expected outcomes stay in the tests.
"""

import functools
from uuid import uuid4

import requests
from requests.adapters import HTTPAdapter

POOL_MAXSIZE = 16


def build_session() -> requests.Session:
    """Build a fresh pooled ``requests.Session``.

    The adapter is mounted for both http and https so the same pool is used
    regardless of the configured ``GTS_BASE_URL`` scheme.
    """
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=POOL_MAXSIZE,
        pool_maxsize=POOL_MAXSIZE,
        max_retries=0,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


@functools.lru_cache(maxsize=1)
def get_session() -> requests.Session:
    """Return a process-wide, lazily-built pooled session singleton."""
    return build_session()


class GtsTestAPI:
    """Raw HTTP access to a GTS server for one test.

    Every test gets a fresh ID namespace, so entities it registers never
    collide with those of other tests or earlier runs against the same server.
    """

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.id_prefix = f"gts.x.pytest.n{uuid4().hex}"

    def type_id(self, name, version="1"):
        """A root type ID in this test's namespace."""
        return f"{self.id_prefix}.{name}.v{version}~"

    @staticmethod
    def derived_type_id(base_type_id, name):
        """A type ID chained to `base_type_id`, i.e. derived from it."""
        return f"{base_type_id}x.pytest._.{name}.v1~"

    def request(self, method, path, status=200, **kwargs):
        response = self.session.request(
            method, self.base_url + path, timeout=30, **kwargs
        )
        assert response.status_code == status, response.text
        return response.json()

    def register(
        self,
        name,
        schema,
        dialect,
        *,
        type_id=None,
        validate=True,
        status=200,
        mode="any-valid",
    ):
        """Registers a type schema; `status=422` expects validation to reject it.

        `$id` and `$schema` are added here; the rest of the schema is sent as
        given.
        """
        type_id = type_id or self.type_id(name)
        result = self.request(
            "POST",
            "/entities",
            status=status,
            params={"validate": str(validate).lower(), "gts-ref-validation": mode},
            json={**schema, "$id": "gts://" + type_id, "$schema": dialect},
        )
        if status == 200:
            assert result["ok"] is True, result
        return type_id

    def register_deferred(self, name, schema, dialect):
        """Registers an invalid schema without validation.

        Returns the type ID, or None if the implementation rejected the schema
        eagerly, which registration without validation does not forbid.
        """
        type_id = self.type_id(name)
        response = self.session.post(
            self.base_url + "/entities",
            params={"validate": "false"},
            json={**schema, "$id": "gts://" + type_id, "$schema": dialect},
            timeout=30,
        )
        assert response.status_code in (200, 422), response.text
        if response.status_code == 422:
            return None
        assert response.json()["ok"] is True, response.text
        return type_id

    def register_instance(
        self,
        type_id,
        payload,
        *,
        name="item",
        validate=False,
        mode="any-valid",
        status=200,
    ):
        """Registers an instance of `type_id`; `status=422` expects rejection."""
        instance_id = f"{type_id}x.pytest._.{name}.v1"
        result = self.request(
            "POST",
            "/entities",
            status=status,
            params={"validate": str(validate).lower(), "gts-ref-validation": mode},
            json={**payload, "id": instance_id, "type": type_id},
        )
        if status == 200:
            assert result["ok"] is True, result
        return instance_id

    @staticmethod
    def verdict(result, valid):
        assert result["ok"] is valid, result
        if not valid:
            assert result.get("error"), result

    def check_transient_schema(self, name, schema, dialect, *, valid):
        """Validates schema JSON with POST /validate-json, without registering it."""
        result = self.request(
            "POST",
            "/validate-json",
            json={**schema, "$id": "gts://" + self.type_id(name), "$schema": dialect},
        )
        assert result["is_type_schema"] is True, result
        self.verdict(result, valid)

    def check_payload(self, type_id, payload, *, valid):
        """Validates an unregistered payload against a registered type."""
        result = self.request("POST", "/validate-json/" + type_id, json=payload)
        self.verdict(result, valid)

    def check_type_schema(self, type_id, *, valid, mode="any-valid"):
        """Validates a registered type schema through both validation endpoints."""
        for endpoint, key in (
            ("validate-type-schema", "type_id"),
            ("validate-entity", "entity_id"),
        ):
            result = self.request(
                "POST",
                "/" + endpoint,
                params={"gts-ref-validation": mode},
                json={key: type_id},
            )
            self.verdict(result, valid)

    def check_instance(self, instance_id, *, valid, mode="any-valid"):
        """Validates a registered instance through both validation endpoints."""
        for endpoint, key in (
            ("validate-instance", "instance_id"),
            ("validate-entity", "entity_id"),
        ):
            result = self.request(
                "POST",
                "/" + endpoint,
                params={"gts-ref-validation": mode},
                json={key: instance_id},
            )
            self.verdict(result, valid)
