FROM registry.access.redhat.com/ubi9/python-311:9.7-1767889564@sha256:99438cd522c6958f0101ee7a35cb7cfeb048e13a20bbe40dd8807ab555961da7 AS base
COPY --from=ghcr.io/astral-sh/uv:0.9.23@sha256:22f6ca040d3f5484d9d792b8de122bb8846760cd997edc73443bc03815cf0a01 /uv /bin/uv

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
