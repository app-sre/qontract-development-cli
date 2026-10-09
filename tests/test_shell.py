from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from qontract_development_cli import shell
from qontract_development_cli.commands import config as config_command
from qontract_development_cli.config import Config

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


@pytest.mark.parametrize("plain", [False, True])
@pytest.mark.parametrize("override", [False, True])
def test_plain_compose_output_is_opt_in(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    plain: bool,
    override: bool,
) -> None:
    monkeypatch.setattr(shell, "_docker_compose_bin", ["docker", "compose"])
    compose = tmp_path / "compose.yml"
    extra = tmp_path / "compose.override.yml"
    if override:
        extra.touch()
    assert shell.compose_command(compose, plain=plain) == [
        "docker",
        "compose",
        *(["--ansi", "never"] if plain else []),
        "-f",
        str(compose),
        *(["-f", str(extra)] if override else []),
    ]


@pytest.mark.parametrize("build", [False, True])
def test_interactive_startup_keeps_compose_output_and_build_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    build: bool,
) -> None:
    monkeypatch.setattr(shell, "_docker_compose_bin", ["docker", "compose"])
    execute = Mock()
    monkeypatch.setattr(subprocess, "run", execute)
    compose = tmp_path / "compose.yml"
    shell.compose_up(compose, build=build)
    execute.assert_called_once_with(
        [
            "docker",
            "compose",
            "-f",
            str(compose),
            "up",
            "-d",
            "--remove-orphans",
            "--build" if build else "--no-build",
        ],
        check=True,
    )


@pytest.mark.parametrize("parent_exists", [False, True])
def test_config_edit_creates_parent_before_opening_editor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    parent_exists: bool,
) -> None:
    config_file = tmp_path / "new-config" / "config.yaml"
    if parent_exists:
        config_file.parent.mkdir()
    config = Config.model_construct(editor="test-editor")
    monkeypatch.setattr(config_command, "user_config_file", config_file)
    monkeypatch.setattr(config_command, "get_config", lambda: config)

    def run_editor(arguments: Sequence[str | Path], *, check: bool) -> None:
        assert config_file.parent.is_dir()
        assert list(arguments) == ["test-editor", config_file]
        assert check is True

    execute = Mock(side_effect=run_editor)
    monkeypatch.setattr(subprocess, "run", execute)
    config_command.edit()
    execute.assert_called_once_with(["test-editor", config_file], check=True)
    assert not config_file.exists()
