FROM registry.access.redhat.com/ubi10/python-314-minimal:10.2-1785358707@sha256:eebdc6df1013280116d9d90a07593b27facbcd75160c611e7f886f0a313a8959 AS base
COPY --from=ghcr.io/astral-sh/uv:0.12.0@sha256:606e70c71c852d03f611b1e56a195d08648507018a7057fab82c4974c4eae105 /uv /bin/uv

COPY LICENSE /licenses/

USER root
RUN microdnf install -y make
USER 1001

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
COPY tests ./tests

# Install dependencies
RUN uv sync --frozen

FROM base AS test
RUN make test

FROM test AS pypi
# Secrets are owned by root and are not readable by others :(
USER root
RUN --mount=type=secret,id=app-sre-pypi-credentials/token make -s pypi
