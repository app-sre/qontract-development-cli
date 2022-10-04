import logging
import subprocess

import typer

from ..config import config, user_config_file
from ..models import DEFAULT_PROFILE, Env
from ..utils import console

app = typer.Typer()
log = logging.getLogger(__name__)


@app.command()
def init():
    """Dump default files (config, environment, profiles)"""
    config.save()
    console.print(f"Config file '[b]{user_config_file}[/]' saved.")
    env = Env(name="dev")
    env.dump()
    console.print(f"Environment file '[b]{env.name}[/]' saved.")
    DEFAULT_PROFILE.dump()
    console.print(f"Defaults profile file '[b]{DEFAULT_PROFILE.name}[/]' saved.")


@app.command()
def edit():
    """Edit config in your editor."""
    console.print(f"Opening [b]{user_config_file}[/] in your editor ...")
    subprocess.run([config.editor, user_config_file])
