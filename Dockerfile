FROM registry.access.redhat.com/ubi9/python-311:9.7-1775651712@sha256:7671c961bb60490b6cdd5c078f9c8ebb0392cddb736f91c22a605eeec00f663e AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.5@sha256:555ac94f9a22e656fc5f2ce5dfee13b04e94d099e46bb8dd3a73ec7263f2e484 /uv /bin/uv

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
