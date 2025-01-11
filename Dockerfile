FROM registry.access.redhat.com/ubi9/python-311:9.5-1734553278@sha256:27d9f910951891b64953fc66fe161ad7a28552fda6e6cb6996db8449f317925e as base
COPY --from=ghcr.io/astral-sh/uv:0.5.17@sha256:9717ecdb1c2fd58eee3fcfd6e2008413a392f31294857500ea4869c87a16d601 /uv /bin/uv

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
