FROM registry.access.redhat.com/ubi9/python-311:1-77.1726664316
COPY --from=ghcr.io/astral-sh/uv:0.4.27 /uv /bin/uv

ARG TWINE_USERNAME
ARG TWINE_PASSWORD
ARG MAKE_TARGET

USER 0
WORKDIR /app
RUN chown -R 1001:0 .

USER 1001

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# other project related files
COPY LICENSE README.md Makefile ./

# the source code
COPY qontract_development_cli ./qontract_development_cli

# Sync the project
RUN uv sync --frozen --no-editable

RUN make $MAKE_TARGET
