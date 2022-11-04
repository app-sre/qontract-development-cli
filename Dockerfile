FROM registry.access.redhat.com/ubi8/python-39
ARG POETRY_VERSION
ARG TWINE_USERNAME
ARG TWINE_PASSWORD
ARG MAKE_TARGET

RUN pip install --upgrade pip && \
    pip install poetry==$POETRY_VERSION
COPY --chown=1000 . .
RUN poetry install
USER 1000
RUN make $MAKE_TARGET
