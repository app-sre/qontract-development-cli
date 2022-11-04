DIRS := qontract_development_cli
BUILD_ARGS := POETRY_VERSION=1.2.2 TWINE_USERNAME TWINE_PASSWORD
# TWINE_USERNAME & TWINE_PASSWORD are available in jenkins job
POETRY_HTTP_BASIC_PYPI_USERNAME := $(TWINE_USERNAME)
POETRY_HTTP_BASIC_PYPI_PASSWORD := $(TWINE_PASSWORD)
export POETRY_HTTP_BASIC_PYPI_USERNAME
export POETRY_HTTP_BASIC_PYPI_PASSWORD

tapes = $(wildcard demo/*.tape)
gifs = $(tapes:%.tape=%.gif)

all:
	@echo $(tapes)
	@echo $(tape_files)
	@echo $(patsubst %.tape,%.c,$(tape_files))

format:
	poetry run black $(DIRS)
.PHONY: format

pr-check:
	docker build -t qontract-development-test --progress plain --build-arg MAKE_TARGET=test $(foreach arg,$(BUILD_ARGS),--build-arg $(arg)) .
.PHONY: pr-check

test:
	poetry run pytest -vv
	poetry run flake8 $(DIRS)
	poetry run mypy $(DIRS)
	poetry run black --check $(DIRS)
.PHONY: test

build-deploy:
	docker build -t qontract-development-test  --progress plain --build-arg MAKE_TARGET=release $(foreach arg,$(BUILD_ARGS),--build-arg $(arg)) .
.PHONY: build-deploy

release:
	git config --global --get user.email || git config --global user.email 'sd-app-sre+ci-ext@redhat.com'
	git config --global --get user.name || git config --global user.name 'AppSRE ci.ext'
	poetry run cz bump --changelog --yes && poetry publish --build
	git push origin master
.PHONY: release

update-demos: $(gifs)

$(gifs): %.gif: %.tape
	ifeq (, $(shell which vhs2))
	$(error "No vhs command not found in $$PATH. Please install https://github.com/charmbracelet/vhs")
	endif
	cd demo && vhs < $(notdir $?)
