FROM registry.access.redhat.com/ubi9/python-311:9.6-1747333117@sha256:82a16d7c4da926081c0a4cc72a84d5ce37859b50a371d2f9364313f66b89adf7 as base
COPY --from=ghcr.io/astral-sh/uv:0.7.6@sha256:c467e9b5da1e763ee5841f9ae51020d11569ca08991a05367ceca6eda0be9b16 /uv /bin/uv

COPY LICENSE /licenses/

ENV \
    # use venv from ubi image
    UV_PROJECT_ENVIRONMENT=$APP_ROOT \
    # disable uv cache. it doesn't make sense in a container
    UV_NO_CACHE=true

COPY pyproject.toml uv.lock ./
# Test lock file is up to date
RUN uv lock --locked
# other project related files
COPY README.md Makefile ./
# the source code
COPY qontract_development_cli ./qontract_development_cli

# Install dependencies
RUN uv sync --frozen

FROM base AS test
RUN make test

FROM test AS pypi
# Secrets are owned by root and are not readable by others :(
USER root
RUN --mount=type=secret,id=app-sre-pypi-credentials/token make -s pypi
