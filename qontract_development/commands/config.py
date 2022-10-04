import logging
import subprocess

import typer
from rich import print

from ..config import config, user_config_file
from ..models import DEFAULT_PROFILE, Env

app = typer.Typer()
log = logging.getLogger(__name__)


@app.command()
def init():
    """Dump default files (config, environment, profiles)"""
    config.save()
    print(f"Config file '[b]{user_config_file}[/]' saved.")
    DEFAULT_PROFILE.dump()
    print(f"Defaults profile file '[b]{DEFAULT_PROFILE.name}[/]' saved.")
    env = Env(name="foobar")
    env.dump()
    print(f"Environment file '[b]{env.name}[/]' saved.")


@app.command()
def edit():
    """Edit config in your editor."""
    subprocess.run([config.editor, user_config_file])
