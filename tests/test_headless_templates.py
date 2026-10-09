from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
import yaml

from qontract_development_cli.models import EnvSettings, ProfileSettings
from qontract_development_cli.templates import template

if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.mark.parametrize("headless", [False, True])
@pytest.mark.parametrize(
    ("filename", "service_name", "expected_check"),
    [
        ("api.yml.j2", "qontract-api", "r['status'] == 'healthy'"),
        ("subscriber.yml.j2", "qontract-api-subscriber", "r.status == 204"),
        ("worker.yml.j2", "qontract-api-worker", "/metrics"),
    ],
)
def test_api_family_healthchecks_use_the_verified_image_interpreter(
    filename: str,
    service_name: str,
    expected_check: str,
    *,
    headless: bool,
) -> None:
    rendered = template(
        filename,
        headless=headless,
        profile=SimpleNamespace(
            settings=ProfileSettings(
                debugger="" if headless else "debugpy",
                localstack_compose_file=None,
            )
        ),
        env=SimpleNamespace(settings=EnvSettings()),
    )
    service = yaml.safe_load(rendered)["services"][service_name]
    probe = service["healthcheck"]["test"]
    assert probe[:3] == ["CMD", "/opt/app-root/bin/python", "-c"]
    assert expected_check in probe[3]
    compile(probe[3], filename, "exec")
    environment = dict(entry.split("=", 1) for entry in service["environment"])
    assert environment["AUTO_RELOAD"] == ("0" if headless else "1")
    assert environment["DEBUGGER_ENABLED"] == ("false" if headless else "true")
    assert not any(key.endswith("_OPTS") for key in environment)


@pytest.mark.parametrize("dry_run", [False, True])
def test_reconcile_propagates_manager_dry_run_and_uses_mounted_source(
    *, dry_run: bool
) -> None:
    rendered = template(
        "reconcile.yml.j2",
        headless=True,
        profile=SimpleNamespace(
            settings=ProfileSettings(
                dry_run=dry_run,
                debugger="",
                integration_name="test",
                localstack_compose_file=None,
            )
        ),
        env=SimpleNamespace(settings=EnvSettings()),
    )
    service = yaml.safe_load(rendered)["services"]["qontract-reconcile"]
    environment = dict(entry.split("=", 1) for entry in service["environment"])
    assert (
        environment["DRY_RUN"]
        == environment["MANAGER_DRY_RUN"]
        == ("--dry-run" if dry_run else "--no-dry-run")
    )
    assert environment["PYTHONUNBUFFERED"] == "1"
    assert environment["PYTHONPATH"] == "/work"
    assert not environment["DEBUGGER"]
    assert environment["RUN_ONCE"] == "1"
    assert "COMMAND_NAME" not in environment
    assert "entrypoint" not in service
    assert service["restart"] == "no"


@pytest.mark.parametrize("headless", [False, True])
@pytest.mark.parametrize(
    ("key", "value"),
    [("PYTHONUNBUFFERED", "0"), ("PYTHONPATH", "/custom/source")],
)
def test_additional_environment_keeps_precedence_over_generated_python_defaults(
    key: str,
    value: str,
    *,
    headless: bool,
) -> None:
    rendered = template(
        "reconcile.yml.j2",
        headless=headless,
        profile=SimpleNamespace(
            settings=ProfileSettings(
                additional_environment={key: value},
                localstack_compose_file=None,
            )
        ),
        env=SimpleNamespace(settings=EnvSettings()),
    )
    service = yaml.safe_load(rendered)["services"]["qontract-reconcile"]
    environment = dict(entry.split("=", 1) for entry in service["environment"])
    assert environment[key] == value


def test_published_worker_image_uses_the_existing_setting() -> None:
    rendered = template(
        "worker.yml.j2",
        headless=True,
        profile=SimpleNamespace(
            settings=ProfileSettings(
                qontract_api_worker_build_image=False,
                qontract_api_worker_image="example/worker:test",
                localstack_compose_file=None,
            )
        ),
        env=SimpleNamespace(settings=EnvSettings()),
    )
    assert (
        yaml.safe_load(rendered)["services"]["qontract-api-worker"]["image"]
        == "example/worker:test"
    )


@pytest.mark.parametrize("headless", [False, True])
def test_opa_disables_watching_only_in_headless_mode(*, headless: bool) -> None:
    rendered = template(
        "opa.yml.j2",
        headless=headless,
        profile=SimpleNamespace(settings=ProfileSettings(localstack_compose_file=None)),
        env=SimpleNamespace(settings=EnvSettings()),
    )
    service = yaml.safe_load(rendered)["services"]["opa"]
    assert ("--watch" in service["command"]) is not headless
    assert service["healthcheck"]["test"][:3] == ["CMD", "/opa", "eval"]


@pytest.mark.parametrize(
    ("filename", "service_name", "expected_prefix"),
    [
        ("server.yml.j2", "qontract-server", ["CMD", "node", "-e"]),
        ("vault.yml.j2", "vault", ["CMD", "vault", "status"]),
    ],
)
def test_supporting_service_healthchecks_are_rendered(
    filename: str,
    service_name: str,
    expected_prefix: Sequence[str],
) -> None:
    rendered = template(
        filename,
        headless=True,
        profile=SimpleNamespace(settings=ProfileSettings(localstack_compose_file=None)),
        env=SimpleNamespace(settings=EnvSettings()),
    )
    service = yaml.safe_load(rendered)["services"][service_name]
    assert service["healthcheck"]["test"][: len(expected_prefix)] == list(
        expected_prefix
    )
