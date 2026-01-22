# Changelog

## v0.16.0 (2025-12-09)

### Features

* Support qontract-api
* Expose more settings
* Make docker container platform configurable. Global setting per environment and overrides per container in the used profile.

## v0.15.8 (2025-10-02)

### Bugfix

* Always shutdown log tail process on exit

## v0.15.7 (2025-08-27)

### Bugfix

* Update internal CA image
* Introduce `internal_redhat_ca_image` setting

## v0.15.6 (2025-08-04)

### Chore

* Use Konflux builds for `qontract-reconcile` and `qontract-server` images
* Bump dependencies

## v0.15.5 (2025-06-02)

### Chore

* Bump dependencies

## v0.15.4 (2024-12-10)

### Chore

* Bump dependencies

## v0.15.3 (2024-12-09)

### Chore

* Use Konflux for CI/CD

## v0.15.2 (2024-12-06)

### Bugfix

* Update default `config.command` because [qontract-reconcile - uv migrations](https://github.com/app-sre/qontract-reconcile/pull/4790) changes the `run-integration` command.

### Chore

* Bump dependencies

## v0.15.1 (2024-10-31)

### Chore

* Update docs

## v0.15.0 (2024-10-31)

### Features

* Python 3.13 support

### Chore

* Upgrade dependencies
* Use [uv](https://docs.astral.sh/uv/) for Python project management

## v0.14.5 (2024-06-19)

### Bugfix

* Fix render bug for docker-compose file.

## v0.14.4 (2024-06-19)

### Bugfix

* Remove `WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8) and no specific platform was requested` log message on Apple Silicon

## v0.14.3 (2024-06-13)

### Chore

* Upgrade `ruff` and other dependencies

## v0.14.2 (2024-03-14)

### Features

* **profile run**: support `--skip-initial-make-bundle` option via profile settings

## v0.14.1 (2024-02-13)

### Bug Fixes

* fix `make bundle` command

## v0.14.0 (2024-02-13)

### Features

* Python 3.11 support and drop 3.9 support
* Support [localstack](https://github.com/localstack/localstack)

### Chore

* Use [ruff](https://docs.astral.sh/ruff/) for code linting and formatting

## v0.13.2 (2023-10-06)

### Bug Fixes

* selinux support

## v0.13.1 (2023-09-25)

### Bug Fixes

* add type hints
* sort `profile ls` output

## v0.13.0 (2023-08-01)

### Bug Fixes

* **docker-compose**: fix qontract-reconcile restart

## v0.12.0 (2023-05-26)

### Features

* --no-dry-run profile run option

## v0.11.0 (2023-04-25)

### Features

* --skip-initial-make-bundle profile run option

## v0.10.0 (2023-03-29)

### Features

* support running arbitrary qontract-reconcile commands

## v0.9.0 (2023-03-21)

### Features

* extra_host profile setting
* support internal RedHat CAs

## v0.8.1 (2023-03-17)

### Bug Fixes

* document release process
* simplify getting compose binary

## v0.8.0 (2023-03-16)

### Bug Fixes

* gitlab_pr_submitter_queue_url as env settings

## v0.7.1 (2023-02-14)

### Bug Fixes

* **docker compose**: support docker compose plugin and compose standalone binary

## v0.7.0 (2023-01-09)

### Features

* support arbitrary environment variables

## v0.6.0 (2022-12-13)

### Features

* **profile run**: monitor app-interface file changes and restart containers

## v0.5.1 (2022-12-12)

## v0.5.0 (2022-11-12)

### Bug Fixes

* **compose-file**: fix empty qontract-reconcile.links list when no other container wants to be started (#14)

### Features

* **docker-compose**: run docker-compose logs in endless loop (#16)

## v0.4.0 (2022-11-04)

### Features

* move project to app-sre organization

## v0.3.0 (2022-10-24)

### Bug Fixes

* consitent logging

### Features

* **profile run**: monitor file changes and restart containers

## v0.2 (2022-10-19)

### Features

* **release**: fix pypi page

## v0.1.1 (2022-10-19)

### Bug Fixes

* **release**: add secret.PYPI_TOKEN

## v0.1 (2022-10-19)

### Bug Fixes

* **profile**: set RUN_ONCE if true otherwise keep it unset
* **profile rm**: autocompletion
* **profile create**: success message
* **config init**: line breaks in screen capture
* **config init**: show default values
* typo in prompts
* remove broken profile render command
* **docker**: always uppercase log level
* **docker-compose**: run_once
* **docker**: avoid uneeded rebuild of containers
* profile dump
* rename python package to qontract-development-cli
* ProfileSettings defaults
* empty defaults

### Features

* **release**: automatic pypi releases
* **doc**: describe config, env, and profile settings
* **config init**: prompt for important settings
* PR/MR support for app-interface, schemas, and reconcile
* **profile**: add app-interface-path setting to profile; enhance profile create
* **profile run**: treat ctrl-c has quit
* **profile run**: --force-build option
* **docker-compose**: named network
* **docker-compose**: display container logs
* **profile run**: keyboard shortcuts
