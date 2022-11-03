FROM registry.access.redhat.com/ubi8/python-39 as test
ARG POETRY_VERSION

RUN pip install --upgrade pip && \
    pip install poetry==$POETRY_VERSION
COPY . .
RUN poetry install
RUN make test

FROM registry.access.redhat.com/ubi8/python-39 as pypi
ARG POETRY_VERSION
ARG TWINE_USERNAME
ARG TWINE_PASSWORD

RUN pip install --upgrade pip && \
    pip install poetry==$POETRY_VERSION
COPY . .
RUN make release
