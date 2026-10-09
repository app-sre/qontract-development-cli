from __future__ import annotations

from importlib.resources import files
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from qontract_development_cli import skill
from qontract_development_cli.cli import app

if TYPE_CHECKING:
    from pathlib import Path


def test_install_skill_without_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QONTRACT_DEVELOPMENT_DEBUG", "not-a-boolean")
    destination = tmp_path / "skills"
    result = CliRunner().invoke(
        app, ["agentic", "skill-install", "--destination", str(destination)]
    )
    assert result.exit_code == 0, result.output
    installed = destination / "qd-integration-dry-run" / "SKILL.md"
    assert installed.is_file()
    assert "name: qd-integration-dry-run" in installed.read_text()
    assert str(installed) in result.output


@pytest.mark.parametrize("skill_name", ["qd-integration-dry-run", "qd-setup"])
def test_skill_install_idempotency_and_automatic_refresh(
    tmp_path: Path, skill_name: str
) -> None:
    runner = CliRunner()
    args = ["agentic", "skill-install", "--destination", str(tmp_path)]
    assert runner.invoke(app, args).exit_code == 0
    installed = tmp_path / skill_name / "SKILL.md"
    original = installed.read_bytes()
    timestamp = installed.stat().st_mtime_ns
    assert runner.invoke(app, args).exit_code == 0
    assert installed.stat().st_mtime_ns == timestamp
    installed.write_text("User-owned content\n")
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert installed.read_bytes() == original


@pytest.mark.parametrize("location", ["destination", "skill", "file"])
def test_skill_install_refuses_symlinks(tmp_path: Path, location: str) -> None:
    target = tmp_path / "target"
    target.mkdir()
    destination = tmp_path / "skills"
    match location:
        case "destination":
            destination.symlink_to(target, target_is_directory=True)
        case "skill":
            destination.mkdir()
            (destination / "qd-integration-dry-run").symlink_to(
                target, target_is_directory=True
            )
        case "file":
            directory = destination / "qd-integration-dry-run"
            directory.mkdir(parents=True)
            (directory / "SKILL.md").symlink_to(target / "keep.md")
    result = CliRunner().invoke(
        app, ["agentic", "skill-install", "--destination", str(destination)]
    )
    assert result.exit_code != 0
    assert "symlink" in result.output.lower()
    assert list(target.iterdir()) == []


@pytest.mark.parametrize("claude_exists", [False, True])
def test_default_installation_uses_shared_and_existing_claude_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    claude_exists: bool,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    claude = tmp_path / ".claude" / "skills"
    if claude_exists:
        claude.mkdir(parents=True)
    result = CliRunner().invoke(app, ["agentic", "skill-install"])
    assert result.exit_code == 0, result.output
    assert (
        tmp_path / ".agents" / "skills" / "qd-integration-dry-run" / "SKILL.md"
    ).is_file()
    assert (claude / "qd-integration-dry-run" / "SKILL.md").is_file() is claude_exists
    assert claude.exists() is claude_exists


def test_manual_destination_replaces_default_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    custom = tmp_path / "custom"
    result = CliRunner().invoke(
        app, ["agentic", "skill-install", "--destination", str(custom)]
    )
    assert result.exit_code == 0, result.output
    assert (custom / "qd-integration-dry-run" / "SKILL.md").is_file()
    assert not (tmp_path / ".agents").exists()
    assert list((tmp_path / ".claude" / "skills").iterdir()) == []


@pytest.mark.parametrize("skill_name", ["qd-integration-dry-run", "qd-setup"])
def test_installer_deploys_every_bundled_skill(tmp_path: Path, skill_name: str) -> None:
    result = CliRunner().invoke(
        app, ["agentic", "skill-install", "--destination", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    installed = tmp_path / skill_name / "SKILL.md"
    assert installed.is_file()
    assert f"name: {skill_name}" in installed.read_text()
    assert str(installed) in result.output


def test_setup_skill_is_updated_without_an_extra_flag(tmp_path: Path) -> None:
    directory = tmp_path / "qd-setup"
    directory.mkdir()
    installed = directory / "SKILL.md"
    installed.write_text("User-owned setup instructions\n")
    args = ["agentic", "skill-install", "--destination", str(tmp_path)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "name: qd-setup" in installed.read_text()


def test_skill_install_has_no_replace_option() -> None:
    result = CliRunner().invoke(app, ["agentic", "skill-install", "--help"])
    assert result.exit_code == 0
    assert "--replace" not in result.output


def test_setup_skill_is_installed_to_both_default_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    claude = tmp_path / ".claude" / "skills"
    claude.mkdir(parents=True)
    result = CliRunner().invoke(app, ["agentic", "skill-install"])
    assert result.exit_code == 0, result.output
    for directory in (tmp_path / ".agents" / "skills", claude):
        assert (directory / "qd-setup" / "SKILL.md").is_file()


def test_setup_skill_covers_private_reconcile_toml_without_reading_credentials() -> (
    None
):
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-setup", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    assert "config.<environment>.toml" in instructions
    assert "Never read" in instructions
    assert "path and existence only" in instructions
    assert "user must edit" in instructions
    assert "Edit qd environment and profile YAML directly" in instructions


def test_setup_skill_uses_verified_appsre_credential_workflows() -> None:
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-setup", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    assert "app-interface-development-environment-setup.md" in instructions
    assert "app-interface-dev-config-toml" in instructions
    assert "app-interface-debug-config-toml" in instructions
    assert "vault login -method=oidc" in instructions
    assert "QAPI_JWT_SECRET_KEY" in instructions
    assert "EXPIRES_DAYS=" in instructions
    assert "user-only" in instructions
    assert "local API's" in instructions


def test_installer_discovers_new_packaged_skills_automatically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_root = tmp_path / "package"
    bundled = package_root / "qontract_development_cli" / "skills"
    for name in ("new-example-skill", "another-skill"):
        directory = bundled / name
        directory.mkdir(parents=True)
        (directory / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Example\n---\n"
        )
    (bundled / "assets-only").mkdir()
    monkeypatch.setattr(skill, "files", lambda package: package_root / package)
    destination = tmp_path / "installed"
    result = CliRunner().invoke(
        app, ["agentic", "skill-install", "--destination", str(destination)]
    )
    assert result.exit_code == 0, result.output
    assert sorted(path.name for path in destination.iterdir()) == [
        "another-skill",
        "new-example-skill",
    ]
    assert "qd-integration-dry-run" not in result.output


def test_dry_run_skill_uses_minimal_cli_preflight_and_approval() -> None:
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-integration-dry-run", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    instructions = " ".join(instructions.split())
    assert "--no-no-dry-run" not in instructions
    assert "Do not use `--no-dry-run`" in instructions
    assert "once" in instructions
    assert "one short sentence" in instructions
    assert "No preparation tables" in instructions
    assert "internal qd Python imports" in instructions
    assert "custom redaction" in instructions
    assert "blanket" in instructions
    assert "additional_environment" in instructions
    assert "intentionally override" in instructions


def test_dry_run_skill_omits_known_routine_warnings_but_keeps_other_findings() -> None:
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-integration-dry-run", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    instructions = " ".join(instructions.split())
    assert "Omit these routine local Docker warnings" in instructions
    assert "mount of type `volume` should not define `bind` option" in instructions
    assert "Memory overcommit must be enabled!" in instructions
    assert "Keep other warnings and unexplained differences" in instructions
    assert "Leave the complete saved logs unchanged" in instructions


def test_dry_run_skill_requests_original_log_excerpts_without_report_boilerplate() -> (
    None
):
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-integration-dry-run", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    instructions = " ".join(instructions.split())
    assert "3-8 relevant original log lines" in instructions
    assert "fenced `text` block" in instructions
    assert "Preserve their wording" in instructions
    assert "Do not add dry-run/not-applied boilerplate" in instructions
    assert "Do not add scope bookkeeping" in instructions
    examples = instructions.partition("## Example outcomes")[2]
    assert "Not applied" not in examples
    assert "Dry-run only" not in examples


def test_dry_run_skill_defines_a_fixed_report_with_evidence_based_fallbacks() -> None:
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-integration-dry-run", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    assert "## Final report (exact format)" in instructions
    report_format = instructions.partition("````markdown\n")[2].partition("\n````")[0]
    report_format = "\n".join(
        " ".join(line.split()) for line in report_format.splitlines()
    )
    fields = [
        "| Execution |",
        "| Proposed changes |",
        "| Local edits |",
        "| Coverage |",
        "| Warnings |",
    ]
    assert "| Field | Result |" in report_format
    positions = [report_format.index(field) for field in fields]
    assert positions == sorted(positions)
    assert report_format.index("**Original logs:**") > positions[-1]
    assert report_format.index("**Artifacts:**") > report_format.index(
        "**Original logs:**"
    )
    instructions = " ".join(instructions.split())
    assert "Omit the entire Warnings row" in instructions
    assert "Undetermined from captured output." in instructions
    assert "No relevant application output." in instructions
    assert "Do not add an introduction or closing commentary" in instructions


def test_dry_run_skill_creates_missing_profiles_without_overwriting_existing_settings() -> (
    None
):
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-integration-dry-run", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    instructions = " ".join(instructions.split())
    assert "create it automatically" in instructions
    assert "normal saved profile" in instructions
    assert "qd profile create PROFILE --integration-name INTEGRATION" in instructions
    assert '--integration-extra-args ""' in instructions
    assert "Do not hand-write profile YAML" in instructions
    assert "Let qd handle defaults and storage" in instructions
    assert "integration_name: INTEGRATION" not in instructions
    assert "Never overwrite existing profiles" in instructions
    assert "required arguments are unknown" in instructions
    assert "Do not edit saved configuration" not in instructions
    assert "invent profiles" not in instructions


def test_dry_run_skill_does_not_bypass_existing_profile_conflicts() -> None:
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-integration-dry-run", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    instructions = " ".join(instructions.split())
    assert "Never delete, truncate, or recreate an existing profile" in instructions
    assert "empty, minimal, incomplete, or invalid" in instructions
    assert "qd profile rm" in instructions
    assert "already exists" in instructions
    assert "stop the creation attempt" in instructions
    assert "ask for explicit approval to edit it" in instructions
    assert "mark that integration `blocked`" in instructions
    assert "not permission to edit or delete existing profiles" in instructions


def test_dry_run_skill_repairs_only_reported_local_schema_permissions_and_records_edits() -> (
    None
):
    instructions = (
        files("qontract_development_cli")
        .joinpath("skills", "qd-integration-dry-run", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    instructions = " ".join(instructions.split())
    assert "Forbidden schemas" in instructions
    assert "selected environment's `app_interface_path`" in instructions
    assert "full absolute path" in instructions
    assert "`$schema: /app-sre/integration-1.yml`" in instructions
    assert "`name` matching the integration" in instructions
    assert "only the schema paths reported as forbidden" in instructions
    assert "preserve existing entries" in instructions
    assert "--no-skip-initial-make-bundle" in instructions
    assert "Do not commit or push app-interface changes" in instructions
    assert "remote GraphQL" in instructions
    assert "Local edits" in instructions
    assert "added schema paths" in instructions
