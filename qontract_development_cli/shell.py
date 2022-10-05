import copy
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def compose_up(
    compose_file: Path, force_recreate: bool = False, remove_orphan: bool = True
) -> None:
    compose_cmd = ["docker-compose", "-f", str(compose_file), "up", "-d"]
    if force_recreate:
        compose_cmd.append("--force-recreate")
    if remove_orphan:
        compose_cmd.append("--remove-orphans")
    subprocess.run(compose_cmd)


def compose_restart(compose_file: Path, container: str) -> None:
    compose_cmd = ["docker-compose", "-f", str(compose_file), "restart", container]
    subprocess.run(compose_cmd)


def compose_down(compose_file: Path) -> None:
    compose_cmd = ["docker-compose", "-f", str(compose_file), "down"]
    subprocess.run(compose_cmd)


def compose_list_projects() -> list[dict[str, Any]]:
    return json.loads(
        subprocess.run(
            ["docker-compose", "ls", "--format", "json"],
            capture_output=True,
            check=True,
        ).stdout
    )


def compose_stop_projects(ignore: str = ""):
    for p in compose_list_projects():
        if p["Name"] != ignore:
            subprocess.run(["docker-compose", "-f", p["ConfigFiles"], "down"])


def make_bundle(app_interface_path: Path, qontract_server_path: Path):
    shell_env = copy.deepcopy(os.environ)
    shell_env.update({"APP_INTERFACE_PATH": str(app_interface_path)})
    subprocess.run(["make", "-C", str(qontract_server_path), "bundle"], env=shell_env)
