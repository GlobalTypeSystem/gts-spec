import os
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


def pytest_sessionstart(session: pytest.Session) -> None:
    """Validate connection to GTS server before running any tests."""
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
