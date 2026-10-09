from __future__ import annotations

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, TypeAdapter

from .templates import template
from .utils import EndlessProcess, console

if TYPE_CHECKING:
    from multiprocessing import Process

    from .models import Profile
    from .process import Runner

log = logging.getLogger(__name__)

_docker_compose_bin = (
    ["docker-compose"] if which("docker-compose") else ["docker", "compose"]
)


def compose_command(compose_file: Path, *, plain: bool = False) -> list[str]:
    """Build the base docker compose command with main and override files."""
    cmd = [*_docker_compose_bin]
    if plain:
        cmd.extend(["--ansi", "never"])
    cmd.extend(["-f", str(compose_file)])
    override = compose_file.parent / "compose.override.yml"
    if override.exists():
        cmd.extend(["-f", str(override)])
    return cmd


def compose_up(
    compose_file: Path,
    *,
    force_recreate: bool = False,
    remove_orphan: bool = True,
    build: bool = False,
) -> None:
    log.info("Starting all containers")
    compose_cmd = [*compose_command(compose_file), "up", "-d"]
    if force_recreate:
        compose_cmd.append("--force-recreate")
    if remove_orphan:
        compose_cmd.append("--remove-orphans")
    if build:
        compose_cmd.append("--build")
    else:
        compose_cmd.append("--no-build")
    subprocess.run(compose_cmd, check=True)


def compose_restart(compose_file: Path, container: str) -> None:
    log.info(f"Restarting {container} container")
    compose_cmd = [*compose_command(compose_file), "restart", container]
    subprocess.run(compose_cmd, check=True)


def container_restart(container: str) -> None:
    log.info(f"Restarting {container} container")
    compose_cmd = ["docker", "restart", container]
    subprocess.run(compose_cmd, check=True)


def compose_down(compose_file: Path) -> None:
    log.info("Stopping all containers")
    compose_cmd = [*compose_command(compose_file), "down"]
    subprocess.run(compose_cmd, check=True)


def compose_log_tail(compose_file: Path) -> Process:
    compose_cmd = [*compose_command(compose_file), "logs", "--follow"]
    p = EndlessProcess(target=subprocess.run, args=(compose_cmd,))
    p.start()
    return p


def kill_log_tail(p: Process, compose_file: Path) -> None:
    p.kill()
    subprocess.run(
        [
            "pkill",
            "-9",
            "-f",
            " ".join([*compose_command(compose_file), "logs"]),
        ],
        check=False,
    )


class ComposeProject(BaseModel, frozen=True):
    name: str = Field(alias="Name")
    config_files: str = Field(alias="ConfigFiles")


def compose_list_projects() -> list[ComposeProject]:
    return TypeAdapter(list[ComposeProject]).validate_json(
        subprocess.run(
            [*_docker_compose_bin, "ls", "--format", "json"],
            capture_output=True,
            check=True,
        ).stdout
    )


def compose_stop_project(project_name: str) -> None:
    log.info("Stopping running projects")
    for p in compose_list_projects():
        if p.name == project_name:
            subprocess.run(
                [*_docker_compose_bin, "-f", p.config_files.split(",")[0], "down"],
                check=True,
            )


def make_bundle(
    app_interface_path: Path,
    qontract_server_path: Path,
    *,
    runner: Runner | None = None,
) -> None:
    log.info("Make bundle")
    arguments = [
        "make",
        "-C",
        str(qontract_server_path.expanduser().absolute()),
        "bundle",
        f"APP_INTERFACE_PATH={app_interface_path.expanduser().absolute()}",
    ]
    if runner is not None:
        runner.note("Building the app-interface bundle")
        runner.run(arguments)
        return
    subprocess.run(arguments, check=True)


def make_bundle_and_restart_server(
    app_interface_path: Path, qontract_server_path: Path, compose_file: Path
) -> None:
    make_bundle(app_interface_path, qontract_server_path)
    compose_restart(compose_file, "qontract-server")


def fetch_pull_requests(
    profile: Profile, worktrees_dir: Path, *, runner: Runner | None = None
) -> None:
    log.info("Preparing worktrees")
    repos: list[dict[str, str]] = []

    if profile.settings.app_interface_pr and profile.settings.app_interface_path:
        wd = (
            worktrees_dir.expanduser().absolute()
            / profile.settings.app_interface_path.name
            / str(profile.settings.app_interface_pr)
        )
        repos.append({
            "workdir": str(wd),
            "dir": str(profile.settings.app_interface_path),
            "pr": str(profile.settings.app_interface_pr),
            "upstream": profile.settings.app_interface_upstream,
        })
        profile.settings.app_interface_path = wd
    if profile.settings.qontract_schemas_pr:
        wd = (
            worktrees_dir.expanduser().absolute()
            / profile.settings.qontract_schemas_path.name
            / str(profile.settings.qontract_schemas_pr)
        )
        repos.append({
            "workdir": str(wd),
            "dir": str(profile.settings.qontract_schemas_path),
            "pr": str(profile.settings.qontract_schemas_pr),
            "upstream": profile.settings.qontract_schemas_upstream,
        })
        profile.settings.qontract_schemas_path = wd
    if profile.settings.qontract_reconcile_pr:
        wd = (
            worktrees_dir.expanduser().absolute()
            / profile.settings.qontract_reconcile_path.name
            / str(profile.settings.qontract_reconcile_pr)
        )
        repos.append({
            "workdir": str(wd),
            "dir": str(profile.settings.qontract_reconcile_path),
            "pr": str(profile.settings.qontract_reconcile_pr),
            "upstream": profile.settings.qontract_reconcile_upstream,
        })
        profile.settings.qontract_reconcile_path = wd

    if not repos:
        return

    with tempfile.TemporaryDirectory(prefix="qd-") as directory:
        shell_file = Path(directory) / "prep-worktree.sh"
        shell_file.write_text(
            template("prep-worktree.sh.j2", repos=repos, worktrees_dir=worktrees_dir)
        )
        if runner is not None:
            runner.run(["bash", str(shell_file)])
            return
        try:
            subprocess.run(
                ["bash", str(shell_file)], check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            console.print(f"--- stdout ---\n{e.stdout}")
            console.print(f"--- stderr ---\n{e.stderr}")
            console.print(e)
            sys.exit(1)
