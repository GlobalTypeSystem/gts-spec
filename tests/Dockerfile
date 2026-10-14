# GTS specification e2e test runner.
#
# Builds a self-contained image with Python + pytest deps that runs the
# gts-spec test suite against an external GTS server. The server is expected
# to be reachable from the container (e.g. via host.docker.internal when the
# server runs on the Docker host).
#
# A pre-built image is published to GHCR for every release; rebuild locally
# only when iterating on the tests themselves. See tests/README.md for the
# tag selection guide (no `latest` tag is published — pin to vX.Y or vX.Y.Z):
#   docker pull ghcr.io/globaltypesystem/gts-spec-tests:v0.11
#
# Build (from the gts-spec repo root):
#   docker build -t gts-spec-tests -f tests/Dockerfile tests
#
# Run against a server on the host (Mac/Docker Desktop):
#   docker run --rm gts-spec-tests --gts-base-url http://host.docker.internal:8000
#
# Run against a server on the host (Linux — host.docker.internal not built-in):
#   docker run --rm --add-host=host.docker.internal:host-gateway \
#       gts-spec-tests --gts-base-url http://host.docker.internal:8000

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /tests

# Install dependencies in a separately cached layer. requirements.txt is
# resolved first with pytest 9, pytest-html 4 and pydantic 1.10.x. HttpRunner
# is then installed separately with --no-deps to bypass its legacy pins.
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt \
 && pip install --no-deps 'httprunner>=4,<5'

# Bundle the test suite so the image is usable standalone. Callers can still
# mount a host directory over /tests to iterate without rebuilding.
COPY . /tests

ENTRYPOINT ["pytest", "-p", "no:cacheprovider"]
CMD ["/tests"]
