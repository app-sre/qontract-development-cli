from types import SimpleNamespace

import pytest
import yaml

from qontract_development_cli.models import EnvSettings, ProfileSettings
from qontract_development_cli.templates import template


def render_reconcile_yml(
    *,
    integration_extra_args: str = "",
    command_extra_args: str = "",
    additional_environment: dict[str, str] | None = None,
) -> str:
    profile = SimpleNamespace(
        settings=ProfileSettings(
            integration_name="test-integration",
            integration_extra_args=integration_extra_args,
            command_extra_args=command_extra_args,
            additional_environment=additional_environment or {},
            localstack_compose_file=None,
        )
    )
    env = SimpleNamespace(settings=EnvSettings())
    return template("reconcile.yml.j2", profile=profile, env=env)


@pytest.mark.parametrize(
    "integration_extra_args",
    [
        # colon-space sequences are YAML mapping indicators when unquoted
        '--keycloak-instances \'{"url": "https://example.com", "secret": {"path": "x"}}\'',
        "--foo bar # not a comment",
    ],
)
def test_integration_extra_args_with_special_chars_produces_valid_yaml(
    integration_extra_args: str,
) -> None:
    rendered = render_reconcile_yml(integration_extra_args=integration_extra_args)

    compose = yaml.safe_load(rendered)

    env_list = compose["services"]["qontract-reconcile"]["environment"]
    assert f"INTEGRATION_EXTRA_ARGS={integration_extra_args}" in env_list


def test_command_extra_args_with_colon_produces_valid_yaml() -> None:
    rendered = render_reconcile_yml(command_extra_args='--config \'{"a": "b"}\'')

    compose = yaml.safe_load(rendered)

    env_list = compose["services"]["qontract-reconcile"]["environment"]
    assert 'COMMAND_EXTRA_ARGS=--config \'{"a": "b"}\'' in env_list


def test_additional_environment_with_colon_produces_valid_yaml() -> None:
    rendered = render_reconcile_yml(
        additional_environment={"FOO": '{"a": "b"}'},
    )

    compose = yaml.safe_load(rendered)

    env_list = compose["services"]["qontract-reconcile"]["environment"]
    assert 'FOO={"a": "b"}' in env_list
