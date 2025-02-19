FROM registry.access.redhat.com/ubi9/python-311:9.5-1737537151@sha256:fc669a67a0ef9016c3376b2851050580b3519affd5ec645d629fd52d2a8b8e4a as base
COPY --from=ghcr.io/astral-sh/uv:0.6.1@sha256:90daa0b4d74ea55c7b8e06d25d3826b1eac66e7994387248e6173dd2b66668e2 /uv /bin/uv

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
