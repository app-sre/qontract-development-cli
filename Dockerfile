FROM registry.access.redhat.com/ubi9/python-311:9.6-1750969934@sha256:47f3998eaf36beb97789d1fe52db4811e02338cc55266638ebb992df48adea86 AS base
COPY --from=ghcr.io/astral-sh/uv:0.7.18@sha256:1bf08b18814f11cc37b5a1566c11570b4bf660f59225cd4e0f3b18d9fb04c277 /uv /bin/uv

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
