import atexit
import logging
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rich_print
from rich.logging import RichHandler

from .commands import config as config_cmd
from .commands import env, profile
from .config import config
from .utils import console, screenshot

app = typer.Typer()
app.add_typer(env.app, name="env", help="Environment related commands.")
app.add_typer(
    config_cmd.app, name="config", help="Qontract Development config related commands."
)
app.add_typer(profile.app, name="profile", help="Profile related commands.")


def version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        rich_print(f"Version: {version('qontract-development-cli')}")
        raise typer.Exit


@app.callback(no_args_is_help=True)
def main(
    *,
    debug: Annotated[bool, typer.Option(help="Enable debug")] = False,
    screen_capture_file: Annotated[Path | None, typer.Option(writable=True)] = None,
    version: Annotated[  # noqa: ARG001
        bool | None, typer.Option(callback=version_callback, help="Display version")
    ] = None,
) -> None:
    logging.basicConfig(
        level="DEBUG" if config.debug or debug else "INFO",
        format="%(name)-20s: %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    if screen_capture_file is not None:
        rich_print(f"Screen recording: {screen_capture_file}")
        # strip $0 and screen_capture_file option
        args = sys.argv[3:]
        console.print(f"$ qd {' '.join(args)}")
        # title = command sub_command
        title = " ".join(args[0:2])
        atexit.register(screenshot, output_file=screen_capture_file, title=title)
