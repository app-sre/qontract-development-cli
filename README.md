# Qontract Development CLI

[![PyPI](https://img.shields.io/pypi/v/qontract-development-cli)][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]
![PyPI - License](https://img.shields.io/pypi/l/qontract-development-cli)

Qontract Development CLI supports your daily [qontract-reconcile][qontract-reconcile] development work.

## Installation

You can install this library from [PyPI][pypi-link] with `pip`:


```shell
$ python3 -m pip install qontract-development-cli
```

or install it with `pipx`:
```shell
$ pipx install qontract-development-cli
```

You can also use `pipx` to run the library without installing it:

```shell
$ pipx run qontract-development-cli
```

## Quickstart

* Create initial configuration
<img src="images/config_init.svg" />

* Edit configuration
<img src="images/config_edit.svg" />

* Edit `dev` environment
<img src="images/env_edit.svg" />

* Display `dev` environment
<img src="images/env_show_dev.svg" />

* Edit `defaults` profile
<img src="images/profile_edit_defaults.svg" />

* Display `defaults` profile
<img src="images/profile_show_defaults.svg" />

* Create a profile `sql-query` to run the `sql-query` integration
<img src="images/profile_create_sql_query.svg" />

* Display `sql-query` profile
<img src="images/profile_show_sql_query.svg" />

* Run `sql-query` profile
<img src="images/profile_run_sql_query.svg" />

## Features

Qontract Development CLI currently provides the following features (get help with `-h` or `--help`):

- Run `qontract-reconcile` and `qontract-server` as docker containers on your local machine
- Support for different environments (dev, prod, ...) via `env` command
- Configure your [qontract-reconcile integration][qontract-reconcile] with the `profile` command
- Bootstrap your initial configurations with the `config` command


[pypi-link]:                https://pypi.org/project/qontract-development-cli/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/qontract-development-cli
[pypi-version]:             https://badge.fury.io/py/qontract-development-cli.svg
[qontract-reconcile]:       https://github.com/app-sre/qontract-reconcile
