FROM registry.access.redhat.com/ubi9/python-311:9.6-1749631027@sha256:ae0aa0e09d9e8fb585a019f0f1e7031d53b0def2bf1934291928b9b52aa465d5 AS base
COPY --from=ghcr.io/astral-sh/uv:0.7.14@sha256:cda0fdc9b6066975ba4c791597870d18bc3a441dfc18ab24c5e888c16e15780c /uv /bin/uv

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
