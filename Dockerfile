FROM registry.access.redhat.com/ubi9/python-311:1-77.1726664316@sha256:3dc479c15b8c8e1e09ca03a6eed59bc2d0f9d2e9291184468460f763999f5bf9 as base
COPY --from=ghcr.io/astral-sh/uv:0.5.7@sha256:23272999edd22e78195509ea3fe380e7632ab39a4c69a340bedaba7555abe20a /uv /bin/uv

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
