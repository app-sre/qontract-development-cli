import logging
import subprocess

import typer
from rich import print
from rich.prompt import Confirm

from ..completions import complete_env
from ..config import config
from ..models import Env

app = typer.Typer()
log = logging.getLogger(__name__)


@app.command()
def edit(env_name: str = typer.Argument(..., help="Env to edit or create.")):
    """Create/edit an environment file in your editor."""
    env = Env(name=env_name)
    subprocess.run([config.editor, env.file])


@app.command()
def ls():
    """List all available environments."""
    print(f"Environments directory: [b]{config.environments_dir}[/]")
    print("[b]Environments:[/]")
    for env in Env.list_all():
        print(f"* {env.name}")


@app.command()
def rm(
    env_name: str = typer.Argument(
        ..., help="Environment to remove.", autocompletion=complete_env
    )
):
    """Remove environment."""
    env = Env(name=env_name, default=True)
    if Confirm.ask(f"Do you really want to remove environment [b red]{env.name}[/]?"):
        env.file.unlink()


@app.command()
def show(
    env_name: str = typer.Argument(
        ..., help="Environment to display.", autocompletion=complete_env
    )
):
    """Display environment."""
    env = Env(name=env_name, default=True)
    print(env.file.read_text())
