from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import typer
from rich.prompt import Prompt

from ..config import get_config, user_config_file
from ..models import Env, get_default_profile
from ..utils import console

app = typer.Typer()
log = logging.getLogger(__name__)


@app.command()
def init() -> None:
    """Dump default files (config, environment, profiles)"""
    # qontract-development config
    config = get_config()
    config.save()
    console.print(f"Config file '[b]{user_config_file}[/]' saved.\n")

    # dev env
    console.print("Creating 'dev' environment ...")
    env = Env(name="dev")
    env.settings.app_interface_path = Path(
        Prompt.ask(
            "local app-interface path",
            default=str(env.settings.app_interface_path),
            console=console,
        )
    )
    env.settings.config = Path(
        Prompt.ask(
            "app-interface config",
            default=str(env.settings.config),
            console=console,
        )
    )
    env.dump()
    console.print(f"Environment file '[b]{env.name}[/]' saved.\n")

    # default profile
    console.print("Creating defaults profile ...")
    default_profile = get_default_profile()
    default_profile.settings.qontract_reconcile_path = Path(
        Prompt.ask(
            "local qontract-reconcile path",
            default=str(default_profile.settings.qontract_reconcile_path),
            console=console,
        )
    )
    default_profile.settings.qontract_schemas_path = Path(
        Prompt.ask(
            "local qontract-schemas path",
            default=str(default_profile.settings.qontract_schemas_path),
            console=console,
        )
    )
    default_profile.settings.qontract_server_path = Path(
        Prompt.ask(
            "local qontract-server path",
            default=str(default_profile.settings.qontract_server_path),
            console=console,
        )
    )
    default_profile.dump()
    console.print(f"Defaults profile file '[b]{default_profile.name}[/]' saved.")


@app.command()
def edit() -> None:
    """Edit config in your editor."""
    user_config_file.parent.mkdir(parents=True, exist_ok=True)
    console.print(f"Opening [b]{user_config_file}[/] in your editor ...")
    subprocess.run([get_config().editor, user_config_file], check=True)
