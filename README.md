# Qontract Development CLI

[![PyPI](https://img.shields.io/pypi/v/qontract-development-cli)][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]
![PyPI - License](https://img.shields.io/pypi/l/qontract-development-cli)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

Qontract Development CLI supports your daily [qontract-reconcile][qontract-reconcile] development work.

## Installation

You can install this library from [PyPI][pypi-link] with `pip`:

```shell
$ python3 -m pip install qontract-development-cli
```

Or install it with `pipx`:
```shell
$ pipx install qontract-development-cli
```

You can also use `pipx` to run the library without installing it:

```shell
$ pipx run qontract-development-cli
```

## Quickstart

* Create initial configuration
  ```shell
  $ qd config init
  ```
  <img src="demo/qd_config_init.gif" />

* Create a profile `sql-query` to run the `sql-query` integration
  ```shell
  $ qd profile create sql-query
  ```
  <img src="demo/qd_profile_create.gif" />

* Run `sql-query` profile
  ```shell
  $ profile run dev sql-query
  ```
  <img src="images/profile_run_sql_query.svg" />

## Features

Qontract Development CLI currently provides the following features (get help with `-h` or `--help`):

- Run `qontract-reconcile` and `qontract-server` as docker containers on your local machine
- Support for different environments (dev, prod, ...) via the `env` command
- Configure your [qontract-reconcile integration][qontract-reconcile] with the `profile` command
- Support pull request reviews (see `profile create`)
- Bootstrap your initial configurations with the `config` command
- Shell autocompletion (see `qd --help`)

## Commands

### Config

Manage global qontract-development CLI configuration.

`qd config [sub-cmd] --help`

* **edit**: open the configuration file in your favorite editor
* **init**: create a default configuration

#### Settings
| **Key**                     | **Description**                       | **Default**                          |
| --------------------------- | ------------------------------------- | ------------------------------------ |
| debug                       | Enable/disable debug mode             | false                                |
| defaults_profile            | Name of defaults profile              | defaults                             |
| docker_compose_project_name | Docker compose project name           | qontract-development                 |
| editor                      | Your favorite editor                  | $EDITOR or vim                       |
| environments_dir            | Directory to store environment files  | User config directory / environments |
| profiles_dir                | Directory to store profile files      | User config directory / profiles     |
| worktrees_dir               | Directory to store git repo worktrees | User cache directory / worktrees     |


## Environments

An environment specifies app-interface instance settings, e.g., **dev** vs. **prod** config and path to the actual app-interface instance.

`qd env [sub-cmd] --help`

* **edit**: Create/edit an environment file in your editor.
* **ls**: List all available environments.
* **rm**: Remove environment.
* **show**: Display environment.


#### Settings

| **Key**                            | **Description**                      | **Default**                                    |
| ---------------------------------- | ------------------------------------ | ---------------------------------------------- |
| **app_interface_path**             | Path to local app-interface instance | ~/workspace/app-interface                      |
| app_interface_state_bucket         | S3 bucket                            | empty                                          |
| app_interface_state_bucket_account | AWS S3 account                       | empty                                          |
| **config**                         | app-interface config                 | ~/workspace/qontract-reconcile/config.dev.toml |
| gitlab_pr_submitter_queue_url      | Gitlab pr submitter queue url        |                                                |
| run_qontract_reconcile             | Run qontract-reconcile container     | true                                           |
| run_qontract_server                | Run qontract-server container        | true                                           |
| run_vault                          | Run vault container                  | false                                          |

> :point_right: **Bold keys** are mandatory or should be customized.

## Profiles

A profile specifies all settings to run a qontract-reconcile integration (e.g., *sql-query*).

`qd profile [sub-cmd] --help`

* **create**: Create a new profile to run an integration.

  Supports the creation of a new profile from an open PR/MR. See `qd profile create --help` for all available options.

* **edit**: Edit a profile in your editor.
* **ls**: List all available profiles.
* **rm**: Remove profile.
* **run**: Run a profile.
* **show**: Display profile.


#### Settings

| **Key**                        | **Description**                                                                                                                                                              | **Default**                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| additional_environment         | Dictionary of additional environment variables to pass to the qontract-reconcile container                                                                                   | `{}`                                        |
| container_uid                  | Change ownership of /recconcile files in container to this user id                                                                                                           | current UID                                 |
| command                        | Command to run in the qontract-reconcile container.                                                                                                                          | `dockerfiles/hack/run-integration.py`       |
| command_extra_args             | Additional arguments to pass to the command.                                                                                                                                 |                                             |
| debugger                       | Python debugger                                                                                                                                                              | `debugpy`                                   |
| dry_run                        | Run --dry-run mode                                                                                                                                                           | `true`                                      |
| extra_hosts                    | List of 'HOSTNAME:IP' mapping entries for qontract-reconcile `/etc/hosts`. See [extra_hosts](https://docs.docker.com/compose/compose-file/#extra_hosts) docker compose file. | `[]`                                        |
| **integration_name**           | Intergration name                                                                                                                                                            |                                             |
| **integration_extra_args**     | Intergration extra arguments                                                                                                                                                 |                                             |
| **internal_redhat_ca**         | Inject Red Hat internal CAs and `REQUESTS_CA_BUNDLE` environment variable                                                                                                    | `false`                                     |
| log_level                      | Log level                                                                                                                                                                    | `info`                                      |
| app_interface_path             | App-interface instance path. (Overrides *env.app_interface_path*)                                                                                                            |                                             |
| app_interface_pr               | App-interface PR/MR number                                                                                                                                                   |                                             |
| app_interface_upstream         | Upstream remote name                                                                                                                                                         | `upstream`                                  |
| qontract_reconcile_build_image | Build qontract-reconcile image                                                                                                                                               | `true`                                      |
| qontract_reconcile_image       | Qontract-reconcile image                                                                                                                                                     | `quay.io/app-sre/qontract-reconcile:latest` |
| qontract_reconcile_path        | Qontract-reconcile path                                                                                                                                                      | `~/workspace/qontract-reconcile`            |
| qontract_reconcile_pr          | Qontract-reconcile PR/MR number                                                                                                                                              |                                             |
| qontract_reconcile_upstream    | Upstream remote name                                                                                                                                                         | `upstream`                                  |
| qontract_server_build_image    | Build qontract-server image                                                                                                                                                  | `true`                                      |
| qontract_server_image          | Qontract-server image                                                                                                                                                        | `quay.io/app-sre/qontract-server:lates`t    |
| qontract_server_path           | Qontract-server path                                                                                                                                                         | `~/workspace/qontract-server`               |
| qontract_schemas_path          | Qontract-schemas path                                                                                                                                                        | `~/workspace/qontract-schemas`              |
| qontract_schemas_pr            | Qontract-schemas PR/MR number                                                                                                                                                |                                             |
| qontract_schemas_upstream      | Upstream remote name                                                                                                                                                         | `upstream`                                  |
| run_once                       | If 'true', execute the integration once and exit                                                                                                                             | `true`                                      |
| sleep_duration_secs            | If not *run_once*, sleep duration until integration runs again                                                                                                               | `10`                                        |

> :point_right: **Bold keys** are mandatory or should be customized.

### PR/MR support

It's a pretty handy feature to create a profile from a pull request (merge request). E.g.:

```shell
$ qd profile create --app-interface PATH_TO_YOUR_LOCAL/app-interface-dev-data --app-interface-pr NUMBER --qontract-schemas-pr NUMBER --qontract-reconcile-pr NUMBER --integration-name glitchtip --integration-extra-args '' glitchtip-pr-check
```

Which results into this profile:

```shell
$ qd profile show glitchtip-pr-check
---
app_interface_path: PATH_TO_YOUR_LOCAL/app-interface-dev-data
app_interface_pr: NUMBER
integration_name: glitchtip
qontract_reconcile_pr: NUMBER
qontract_schemas_pr: NUMBER
```

Running this profile will:
* Create new git worktrees (see `config.worktrees_dir`) for app-interface-dev-data, qontract-schema, and qontract-reconcile PRs
* Start the containers with the adapted path to these worktrees
* Restarting the profile will fetch PR updates

> :point_right: A git worktree cleanup isn't implemented yet

## Development

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

### Commits

Use [Conventional Commit messages](https://www.conventionalcommits.org).
The most important prefixes you should have in mind are:

* `fix:` which represents bug fixes and correlates to a [SemVer](https://semver.org/) patch.
* `feat` represents a new feature and correlates to a SemVer minor.
* `feat!:`,  or `fix!:`, `refactor!:`, etc., which represent a breaking change
  (indicated by the `!`) and will result in a SemVer major.

### Release

To release a new version, run:

```shell
$ make release
```

This will:
* Bump the version in `pyproject.toml`
* Update the `CHANGELOG.md`
* Commit the changes


[pypi-link]:                https://pypi.org/project/qontract-development-cli/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/qontract-development-cli
[pypi-version]:             https://badge.fury.io/py/qontract-development-cli.svg
[qontract-reconcile]:       https://github.com/app-sre/qontract-reconcile
