from __future__ import annotations

import signal
import subprocess
from typing import TYPE_CHECKING
from unittest.mock import Mock, call

import pytest
from rich.prompt import Prompt
from typer.testing import CliRunner

from qontract_development_cli import headless, models, orchestration, shell
from qontract_development_cli.cli import app
from qontract_development_cli.commands import profile
from qontract_development_cli.config import Config
from qontract_development_cli.headless import RunOptions
from qontract_development_cli.process import (
    RunInterruptedError,
    Runner,
    RunTimeoutError,
    SetupError,
)
from qontract_development_cli.report import Execution, Outcome, RunReport

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


@pytest.fixture
def runner(saved_config: Config, monkeypatch: pytest.MonkeyPatch) -> Mock:
    result = Mock(spec=Runner)
    result.setup_log = saved_config.environments_dir.parent / "results" / "setup.log"
    result.remaining.return_value = 600
    result.run.return_value = 0
    monkeypatch.setattr(headless, "Runner", Mock(return_value=result))
    monkeypatch.setattr(shell, "_docker_compose_bin", ["docker", "compose"])
    monkeypatch.setattr(
        subprocess,
        "Popen",
        Mock(side_effect=AssertionError("Unit tests must not start external commands")),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(side_effect=AssertionError("Unit tests must not start external commands")),
    )
    return result


@pytest.fixture
def options(tmp_path: Path) -> RunOptions:
    return RunOptions(
        env_name="test", profile_name="test", output_dir=tmp_path / "results"
    )


@pytest.fixture
def saved_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    config = Config.model_construct(
        environments_dir=tmp_path / "environments",
        profiles_dir=tmp_path / "profiles",
        worktrees_dir=tmp_path / "worktrees",
    )
    config.environments_dir.mkdir()
    config.profiles_dir.mkdir()
    (config.environments_dir / "test.yml").write_text(
        "app_interface_path: /test/app-interface\n"
        "run_qontract_api: true\nrun_qontract_api_subscriber: true\n"
        "run_qontract_api_worker: true\nrun_cache: true\n",
    )
    (config.profiles_dir / "defaults.yml").write_text(
        "dry_run: false\ndebugger: debugpy\nrun_once: false\n"
        "skip_initial_make_bundle: true\n",
    )
    (config.profiles_dir / "test.yml").write_text(
        "integration_name: test-integration\n"
    )
    monkeypatch.setattr(models, "get_config", lambda: config)
    monkeypatch.setattr(orchestration, "get_config", lambda: config)
    return config


@pytest.fixture(params=["environment", "profile", "defaults"])
def settings_file(request: pytest.FixtureRequest, saved_config: Config) -> Path:
    if request.param == "environment":
        return saved_config.environments_dir / "test.yml"
    return saved_config.profiles_dir / (
        "defaults.yml" if request.param == "defaults" else "test.yml"
    )


@pytest.mark.parametrize("exit_code", [0, 7])
@pytest.mark.parametrize("force_build", [False, True])
def test_full_stack_lifecycle_and_cached_build_policy(
    runner: Mock, *, exit_code: int, force_build: bool
) -> None:
    options = RunOptions(
        env_name="test",
        profile_name="test",
        output_dir=runner.setup_log.parent,
        force_build=force_build,
    )
    runner.run.side_effect = [0, *([0] if force_build else []), 0, exit_code, 0, 0]
    assert headless.run_headless(options) == exit_code
    execution = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    ).execution
    first = runner.run.call_args_list[0].args[0]
    compose = first[: first.index("down")]
    down = [*compose, "down", "--remove-orphans", "--timeout", "1"]
    assert runner.run.call_args_list == [
        call(down),
        *([call([*compose, "build"])] if force_build else []),
        call([
            *compose,
            "up",
            "--wait",
            "--wait-timeout",
            "600",
            "--no-build",
            "--pull",
            "missing",
            "--remove-orphans",
            "--scale",
            "qontract-reconcile=0",
        ]),
        call(
            [
                *compose,
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "--interactive=false",
                "--pull",
                "never",
                "qontract-reconcile",
            ],
            destination=runner.setup_log.parent / "integration.log",
            check=False,
        ),
        call(
            [*compose, "logs", "--no-color", "--timestamps"],
            destination=runner.setup_log.parent / "stack.log",
        ),
        call(down),
    ]
    assert execution.exit_code == execution.integration_exit_code == exit_code
    assert execution.outcome == (
        Outcome.SUCCESS if exit_code == 0 else Outcome.INTEGRATION_FAILURE
    )
    assert execution.cleanup_completed is True
    assert execution.errors == []


def test_failed_dependency_startup_does_not_launch_integration(
    options: RunOptions,
    runner: Mock,
) -> None:
    runner.run.side_effect = [0, SetupError("dependency unhealthy"), 0, 0]
    assert headless.run_headless(options) == headless.SETUP_EXIT
    execution = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    ).execution
    assert execution.outcome == Outcome.SETUP_FAILURE
    assert execution.integration_exit_code is None
    assert execution.cleanup_completed is True
    assert execution.errors == ["dependency unhealthy"]
    operation_index = runner.run.call_args_list[0].args[0].index("down")
    assert [
        command.args[0][operation_index] for command in runner.run.call_args_list
    ] == ["down", "up", "logs", "down"]


@pytest.mark.parametrize("operation", [1, 2], ids=["startup", "integration"])
@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (
            RunTimeoutError("deadline exceeded"),
            Execution(outcome=Outcome.TIMEOUT, exit_code=124),
        ),
        (
            RunInterruptedError(signal.SIGTERM, location="test"),
            Execution(
                outcome=Outcome.INTERRUPTED, exit_code=143, signal=signal.SIGTERM
            ),
        ),
    ],
)
def test_timeout_and_interrupt_always_collect_logs_and_tear_down(
    options: RunOptions,
    runner: Mock,
    operation: int,
    failure: Exception,
    expected: Execution,
) -> None:
    runner.run.side_effect = [*([0] * operation), failure, 0, 0]
    assert headless.run_headless(options) == expected.exit_code
    execution = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    ).execution
    assert execution.outcome == expected.outcome
    assert execution.exit_code == expected.exit_code
    assert execution.signal == expected.signal
    assert execution.cleanup_completed is True
    assert "logs" in runner.run.call_args_list[-2].args[0]
    assert "down" in runner.run.call_args_list[-1].args[0]


@pytest.mark.parametrize("integration_exit", [0, 7])
@pytest.mark.parametrize("failed_phase", ["logs", "down"])
def test_cleanup_errors_are_reported_without_losing_integration_exit(
    options: RunOptions,
    runner: Mock,
    *,
    integration_exit: int,
    failed_phase: str,
) -> None:
    runner.run.side_effect = [
        0,
        0,
        integration_exit,
        SetupError("logs failed") if failed_phase == "logs" else 0,
        SetupError("down failed") if failed_phase == "down" else 0,
    ]
    expected_exit = headless.CLEANUP_EXIT if integration_exit == 0 else integration_exit
    assert headless.run_headless(options) == expected_exit
    execution = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    ).execution
    assert execution.exit_code == expected_exit
    assert execution.integration_exit_code == integration_exit
    assert execution.cleanup_completed is (failed_phase != "down")
    assert len(execution.errors) == 1
    assert f"{failed_phase} failed" in execution.errors[0]
    assert "down" in runner.run.call_args_list[-1].args[0]


def test_public_run_forces_runtime_settings_without_changing_saved_yaml(
    options: RunOptions,
    runner: Mock,
    saved_config: Config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_files = [
        *saved_config.environments_dir.glob("*.yml"),
        *saved_config.profiles_dir.glob("*.yml"),
    ]
    before = [path.read_bytes() for path in saved_files]
    prepare = Mock(wraps=orchestration.prepare_run)
    monkeypatch.setattr(headless, "prepare_run", prepare)
    assert headless.run_headless(options) == 0
    settings = prepare.call_args.args[1].settings
    assert settings.dry_run is True
    assert settings.run_once is True
    assert not settings.debugger
    assert prepare.call_args.kwargs == {"headless": True, "runner": runner}
    assert [path.read_bytes() for path in saved_files] == before
    report = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    )
    assert report.execution.outcome == Outcome.SUCCESS
    assert report.execution.cleanup_completed is True
    assert report.environment == report.profile == "test"
    assert report.setup_log == options.output_dir / "setup.log"
    assert report.integration_log == options.output_dir / "integration.log"
    assert report.stack_log == options.output_dir / "stack.log"


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_invalid_deadline_does_not_resolve_profiles_or_start_commands(
    tmp_path: Path,
    runner: Mock,
    monkeypatch: pytest.MonkeyPatch,
    timeout: float,
) -> None:
    resolve = Mock()
    monkeypatch.setattr(headless, "resolve_run", resolve)
    options = RunOptions(
        env_name="test",
        profile_name="test",
        output_dir=tmp_path / "results",
        timeout=timeout,
    )
    assert headless.run_headless(options) == headless.SETUP_EXIT
    resolve.assert_not_called()
    runner.run.assert_not_called()


def test_existing_output_is_not_overwritten(
    options: RunOptions,
    runner: Mock,
) -> None:
    options.output_dir.mkdir()
    artifact = options.output_dir / "integration.log"
    artifact.write_text("keep this\n")
    assert headless.run_headless(options) == headless.SETUP_EXIT
    assert artifact.read_text() == "keep this\n"
    runner.run.assert_not_called()


def test_missing_saved_profile_is_reported_without_external_commands(
    options: RunOptions,
    runner: Mock,
    saved_config: Config,
) -> None:
    (saved_config.profiles_dir / "test.yml").unlink()
    assert headless.run_headless(options) == headless.SETUP_EXIT
    report = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    )
    assert report.execution.errors == ["Missing saved environment/profile: test"]
    assert report.execution.integration_exit_code is None
    runner.run.assert_not_called()


@pytest.mark.parametrize(
    "content",
    [
        "",
        "# No settings yet\n",
        "[]\n",
        "example\n",
        "1: example\n",
        "- [integration_name, example]\n",
    ],
    ids=["empty", "comments", "list", "scalar", "non-string-key", "list-of-pairs"],
)
def test_invalid_yaml_shapes_produce_a_setup_failure_report(
    options: RunOptions,
    runner: Mock,
    settings_file: Path,
    content: str,
) -> None:
    settings_file.write_text(content, encoding="utf-8")
    assert headless.run_headless(options) == headless.SETUP_EXIT
    execution = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    ).execution
    assert execution.outcome == Outcome.SETUP_FAILURE
    assert execution.integration_exit_code is None
    assert execution.cleanup_completed is False
    assert execution.errors == [
        "Invalid qd settings; inspect the environment/profile YAML"
    ]
    assert settings_file.read_text(encoding="utf-8") == content
    runner.run.assert_not_called()


def test_empty_yaml_mapping_preserves_settings_defaults(
    options: RunOptions,
    runner: Mock,
    settings_file: Path,
) -> None:
    settings_file.write_text("{}\n", encoding="utf-8")
    assert headless.run_headless(options) == 0
    execution = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    ).execution
    assert execution.outcome == Outcome.SUCCESS
    assert execution.errors == []
    assert settings_file.read_text(encoding="utf-8") == "{}\n"
    assert runner.run.called


@pytest.mark.parametrize(
    ("extra", "error"),
    [
        (["--headless"], "--headless requires --output-dir"),
        (["--output-dir", "results"], "--output-dir requires --headless"),
    ],
)
def test_cli_requires_matching_headless_output_options(
    extra: Sequence[str],
    error: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execute = Mock()
    monkeypatch.setattr(profile, "run_headless", execute)
    result = CliRunner().invoke(app, ["profile", "run", "test", "test", *extra])
    assert result.exit_code != 0
    assert error in result.output
    execute.assert_not_called()


@pytest.mark.parametrize("flag", ["--force-rebuild", "--force-build"])
def test_cli_build_aliases_select_headless_cached_build(
    options: RunOptions,
    monkeypatch: pytest.MonkeyPatch,
    flag: str,
) -> None:
    execute = Mock(return_value=0)
    monkeypatch.setattr(profile, "run_headless", execute)
    result = CliRunner().invoke(
        app,
        [
            "profile",
            "run",
            "test",
            "test",
            "--headless",
            flag,
            "--output-dir",
            str(options.output_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    execute.assert_called_once_with(
        RunOptions(
            env_name="test",
            profile_name="test",
            output_dir=options.output_dir,
            force_build=True,
        )
    )


@pytest.mark.parametrize("extra_args", ["", "--foo bar"])
def test_profile_create_is_noninteractive_when_both_integration_options_are_supplied(
    saved_config: Config,
    monkeypatch: pytest.MonkeyPatch,
    extra_args: str,
) -> None:
    existing = saved_config.profiles_dir / "test.yml"
    defaults = saved_config.profiles_dir / "defaults.yml"
    before = (existing.read_bytes(), defaults.read_bytes())
    prompt = Mock(side_effect=AssertionError("Profile creation must not prompt"))
    monkeypatch.setattr(Prompt, "ask", prompt)
    result = CliRunner().invoke(
        app,
        [
            "profile",
            "create",
            "new-integration",
            "--integration-name",
            "new-integration",
            "--integration-extra-args",
            extra_args,
        ],
    )
    assert result.exit_code == 0, result.output
    created = models.Profile(name="new-integration")
    assert created.file.is_file()
    assert created.settings.integration_name == "new-integration"
    assert created.settings.integration_extra_args == extra_args
    assert (existing.read_bytes(), defaults.read_bytes()) == before
    prompt.assert_not_called()


@pytest.mark.parametrize("content", ["integration_name: change-owners\n", "{}\n", ""])
def test_profile_create_refuses_existing_profiles_without_changing_their_contents(
    saved_config: Config,
    content: str,
) -> None:
    existing = saved_config.profiles_dir / "change-owners.yml"
    existing.write_text(content, encoding="utf-8")
    result = CliRunner().invoke(
        app,
        [
            "profile",
            "create",
            "change-owners",
            "--integration-name",
            "change-owners",
            "--integration-extra-args",
            "13582 210506",
        ],
    )
    assert result.exit_code != 0
    if content:
        assert "already exists" in result.output
    assert existing.is_file()
    assert existing.read_text(encoding="utf-8") == content


def test_cli_rejects_wet_run_before_loading_settings(
    options: RunOptions,
    runner: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolve = Mock()
    monkeypatch.setattr(headless, "resolve_run", resolve)
    result = CliRunner().invoke(
        app,
        [
            "profile",
            "run",
            "test",
            "test",
            "--headless",
            "--no-dry-run",
            "--output-dir",
            str(options.output_dir),
        ],
    )
    assert result.exit_code == headless.SETUP_EXIT
    report = RunReport.model_validate_json(
        (options.output_dir / "result.json").read_text()
    )
    assert report.execution.errors == ["--headless rejects --no-dry-run"]
    resolve.assert_not_called()
    runner.run.assert_not_called()
