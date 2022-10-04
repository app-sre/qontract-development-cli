import logging

import typer
from rich.logging import RichHandler

from .commands import config as config_cmd
from .commands import env, profile
from .config import config

app = typer.Typer()
app.add_typer(env.app, name="env", help="Environment related commands.")
app.add_typer(
    config_cmd.app, name="config", help="Qontract Development config related commands."
)
app.add_typer(profile.app, name="profile", help="Profile related commands.")


@app.callback(no_args_is_help=True)
def main(debug: bool = typer.Option(False, help="Enable debug")):
    logging.basicConfig(
        level="DEBUG" if config.debug or debug else "ERROR",
        format="%(name)-20s: %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
