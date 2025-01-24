FROM registry.access.redhat.com/ubi9/python-311:9.5-1736353526@sha256:35ccd57ca532411cf89746596ee1981102121321152997f14649d7e52845f2e1 as base
COPY --from=ghcr.io/astral-sh/uv:0.5.24@sha256:2381d6aa60c326b71fd40023f921a0a3b8f91b14d5db6b90402e65a635053709 /uv /bin/uv

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
