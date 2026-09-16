import os

# HttpRunner synchronously POSTs to Google Analytics (and inits Sentry) on
# every test_start, adding ~0.5s per test (up to its 5s timeout if the network
# is blocked). Opt out before httprunner is imported anywhere.
os.environ.setdefault("DISABLE_GA", "true")
os.environ.setdefault("DISABLE_SENTRY", "true")

import sys
import typing
import pytest
import requests

from .helpers.http_client import get_session


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--gts-base-url",
        action="store",
        default=None,
        help="Base URL for GTS tests.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Propagate CLI option to env so class-level code can access it."""
    cli_opt = config.getoption("--gts-base-url")
    if cli_opt:
        os.environ["GTS_BASE_URL"] = cli_opt


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: typing.List[pytest.Item]
) -> None:
    """Validate connection to GTS server before running server-dependent tests.

    Pure unit tests (marked ``@pytest.mark.unit``) need no server, so a run that
    selects only unit tests (e.g. ``pytest tests -m unit``) skips the probe
    entirely and can run offline. Any run that includes a server-dependent test
    still fails loudly if the server is unreachable.

    ``trylast=True`` is required so this hook runs *after* pytest's built-in
    ``-m``/``-k`` deselection: otherwise ``items`` would still contain the
    server-dependent tests that the expression is filtering out, and a
    ``-m unit`` run would probe the server anyway.
    """
    if not items or all(item.get_closest_marker("unit") for item in items):
        return

    url = get_gts_base_url() + "/entities"
    try:
        response = get_session().get(url, timeout=5)
        response.raise_for_status()
        print(f"\nSuccessfully connected to GTS server at {url}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"\nFailed to connect to GTS server at {url} : {e}", file=sys.stderr)
        print(f"Please ensure the GTS server is running before executing tests.", file=sys.stderr)
        pytest.exit("GTS server connection failed", returncode=1)


def get_gts_base_url() -> str:
    """Get GTS base URL: env var (set by CLI or user), or default http://127.0.0.1:8000."""
    url = os.getenv("GTS_BASE_URL", "http://127.0.0.1:8000")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url


def pytest_runtest_teardown(item: pytest.Item, nextitem: typing.Optional[pytest.Item]) -> None:
    try:
        from loguru import logger
    except Exception:
        return

    try:
        logger.remove()
    except Exception:
        return


@pytest.fixture(scope="session")
def gts_base_url(pytestconfig: pytest.Config) -> str:
    """GTS base URL fixture with CLI override support."""
    return pytestconfig.getoption("--gts-base-url") or get_gts_base_url()


@pytest.fixture(scope="session")
def gts_session() -> typing.Iterator[requests.Session]:
    """Session-scoped, connection-pooled HTTP client shared across tests."""
    session = get_session()
    yield session
    session.close()
    get_session.cache_clear()
