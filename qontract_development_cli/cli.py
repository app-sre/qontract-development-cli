import atexit
import logging
import sys
from pathlib import Path

import typer
from rich.logging import RichHandler

from .commands import config as config_cmd
from .commands import (
    env,
    profile,
)
from .config import config
from .utils import (
    console,
    screenshot,
)

app = typer.Typer()
app.add_typer(env.app, name="env", help="Environment related commands.")
app.add_typer(
    config_cmd.app, name="config", help="Qontract Development config related commands."
)
app.add_typer(profile.app, name="profile", help="Profile related commands.")


@app.callback(no_args_is_help=True)
def main(
    debug: bool = typer.Option(False, help="Enable debug"),
    screen_capture_file: Path = typer.Option(None, writable=True),
):
    logging.basicConfig(
        level="DEBUG" if config.debug or debug else "INFO",
        format="%(name)-20s: %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    if screen_capture_file is not None:
        print(f"Screen recording: {screen_capture_file}")
        # strip $0 and screen_capture_file option
        args = sys.argv[3:]
        console.print(f"$ qd {' '.join(args)}")
        # title = command sub_command
        title = " ".join(args[0:2])
        atexit.register(screenshot, output_file=screen_capture_file, title=title)
