UV_RUN := uv run --frozen

tapes = $(wildcard demo/*.tape)
gifs = $(tapes:%.tape=%.gif)

format:
	$(UV_RUN) ruff check
	$(UV_RUN) ruff format
.PHONY: format

test:
	$(UV_RUN) qd --version
	$(UV_RUN) ruff check --no-fix
	$(UV_RUN) ruff format --check
	$(UV_RUN) mypy
.PHONY: test

# do not print pypi commands to avoid the token leaking to the logs
.SILENT: pypi
pypi:
	uv build --sdist --wheel
	UV_PUBLISH_TOKEN=$(shell cat /run/secrets/app-sre-pypi-credentials/token) \
		uv publish
.PHONY: pypi

update-demos: $(gifs)

$(gifs): %.gif: %.tape
	ifeq (, $(shell which vhs2))
	$(error "No vhs command not found in $$PATH. Please install https://github.com/charmbracelet/vhs")
	endif
	cd demo && vhs < $(notdir $?)
