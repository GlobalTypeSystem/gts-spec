"""Shared, connection-pooled HTTP client for the GTS test suite.

Module-level ``requests.get`` / ``requests.post`` helpers create and discard a
fresh ``Session`` on every call, so each request pays a new TCP (and TLS)
handshake. Reusing a single ``requests.Session`` with a mounted ``HTTPAdapter``
enables keep-alive connection reuse across all the raw request call sites in the
suite (conftest probe, the OP#2 plain-function tests, and generate_examples).

Conformance tests assert exact server status codes, so the adapter is configured
with ``max_retries=0``: connections are pooled, but responses are never retried
or masked.
"""

import functools

import requests
from requests.adapters import HTTPAdapter


def build_session(pool_maxsize: int = 16) -> requests.Session:
    """Build a fresh pooled ``requests.Session``.

    The adapter is mounted for both http and https so the same pool is used
    regardless of the configured ``GTS_BASE_URL`` scheme.
    """
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=pool_maxsize,
        pool_maxsize=pool_maxsize,
        max_retries=0,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


@functools.lru_cache(maxsize=1)
def get_session() -> requests.Session:
    """Return a process-wide, lazily-built pooled session singleton."""
    return build_session()
