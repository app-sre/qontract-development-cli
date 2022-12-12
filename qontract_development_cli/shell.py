import copy
import json
import logging
import os
import subprocess
import sys
import tempfile
from multiprocessing import Process
from pathlib import Path
from typing import Any

from .models import Profile
from .templates import template
from .utils import (
    EndlessProcess,
    console,
)

log = logging.getLogger(__name__)


def compose_up(
    compose_file: Path,
    force_recreate: bool = False,
    remove_orphan: bool = True,
    build: bool = False,
) -> None:
    log.info("Starting all containers")
    compose_cmd = ["docker-compose", "-f", str(compose_file), "up", "-d"]
    if force_recreate:
        compose_cmd.append("--force-recreate")
    if remove_orphan:
        compose_cmd.append("--remove-orphans")
    if build:
        compose_cmd.append("--build")
    subprocess.run(compose_cmd)


def compose_restart(compose_file: Path, container: str) -> None:
    log.info(f"Restarting {container} container")
    compose_cmd = ["docker-compose", "-f", str(compose_file), "restart", container]
    subprocess.run(compose_cmd)


def compose_down(compose_file: Path) -> None:
    log.info("Stopping all containers")
    compose_cmd = ["docker-compose", "-f", str(compose_file), "down"]
    subprocess.run(compose_cmd)


def compose_log_tail(compose_file: Path) -> Process:
    compose_cmd = ["docker-compose", "-f", str(compose_file), "logs", "--follow"]
    p = EndlessProcess(target=subprocess.run, args=(compose_cmd,))
    p.start()
    return p


def compose_list_projects() -> list[dict[str, Any]]:
    return json.loads(
        subprocess.run(
            ["docker-compose", "ls", "--format", "json"],
            capture_output=True,
            check=True,
        ).stdout
    )


def compose_stop_project(project_name: str):
    log.info("Stopping running projects")
    for p in compose_list_projects():
        if p["Name"] == project_name:
            subprocess.run(["docker-compose", "-f", p["ConfigFiles"], "down"])


def make_bundle(app_interface_path: Path, qontract_server_path: Path):
    log.info("Make bundle")
    shell_env = copy.deepcopy(os.environ)
    shell_env.update(
        {"APP_INTERFACE_PATH": str(app_interface_path.expanduser().absolute())}
    )
    subprocess.run(["make", "-C", str(qontract_server_path), "bundle"], env=shell_env)


def make_bundle_and_restart_server(
    app_interface_path: Path, qontract_server_path: Path, compose_file: Path
):
    make_bundle(app_interface_path, qontract_server_path)
    compose_restart(compose_file, "qontract-server")


def fetch_pull_requests(profile: Profile, worktrees_dir: Path):
    log.info("Preparing worktrees")
    repos: list[dict[str, str]] = []

    if profile.settings.app_interface_pr and profile.settings.app_interface_path:
        wd = (
            worktrees_dir.expanduser().absolute()
            / profile.settings.app_interface_path.name
            / str(profile.settings.app_interface_pr)
        )
        repos.append(
            {
                "workdir": str(wd),
                "dir": str(profile.settings.app_interface_path),
                "pr": str(profile.settings.app_interface_pr),
                "upstream": profile.settings.app_interface_upstream,
            }
        )
        profile.settings.app_interface_path = wd
    if profile.settings.qontract_schemas_pr:
        wd = (
            worktrees_dir.expanduser().absolute()
            / profile.settings.qontract_schemas_path.name
            / str(profile.settings.qontract_schemas_pr)
        )
        repos.append(
            {
                "workdir": str(wd),
                "dir": str(profile.settings.qontract_schemas_path),
                "pr": str(profile.settings.qontract_schemas_pr),
                "upstream": profile.settings.qontract_schemas_upstream,
            }
        )
        profile.settings.qontract_schemas_path = wd
    if profile.settings.qontract_reconcile_pr:
        wd = (
            worktrees_dir.expanduser().absolute()
            / profile.settings.qontract_reconcile_path.name
            / str(profile.settings.qontract_reconcile_pr)
        )
        repos.append(
            {
                "workdir": str(wd),
                "dir": str(profile.settings.qontract_reconcile_path),
                "pr": str(profile.settings.qontract_reconcile_pr),
                "upstream": profile.settings.qontract_reconcile_upstream,
            }
        )
        profile.settings.qontract_reconcile_path = wd

    if not repos:
        return

    tmp_dir = Path(tempfile.mkdtemp(prefix="qd-"))
    shell_file = tmp_dir / "prep-worktree.sh"
    shell_file.write_text(
        template("prep-worktree.sh.j2", repos=repos, worktrees_dir=worktrees_dir)
    )
    try:
        subprocess.run(
            ["bash", str(shell_file)], check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        console.print(f"--- stdout ---\n{e.stdout}")
        console.print(f"--- stderr ---\n{e.stderr}")
        console.print(e)
        sys.exit(1)
