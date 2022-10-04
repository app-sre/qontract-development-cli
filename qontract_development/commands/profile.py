import logging
import subprocess
import sys
import tempfile
from pathlib import Path

import typer
from rich import print
from rich.prompt import Confirm, Prompt

from ..completions import complete_env, complete_profile
from ..config import config
from ..models import Env, Profile
from ..shell import compose_stop_projects, compose_up, make_bundle
from ..templates import template

app = typer.Typer()
log = logging.getLogger(__name__)


@app.command()
def create(profile_name: str = typer.Argument(..., help="Profile to create.")):
    """Create a new profile."""
    if profile_name in [p.name for p in Profile.list_all()]:
        print(
            f"[b red]Profile {profile_name} already exists![/] Choose another profile name."
        )
        sys.exit(1)
    profile = Profile(name=profile_name)
    profile.settings.integration_name = Prompt.ask("Integration name")
    profile.settings.integration_extra_args = Prompt.ask(
        "Integration extra arguments", default=""
    )
    profile.dump()


@app.command()
def edit(
    profile_name: str = typer.Argument(
        ..., help="Profile to edit.", autocompletion=complete_profile
    )
):
    """Edit a profile in your editor."""
    profile = Profile(name=profile_name, default=True)
    subprocess.run([config.editor, profile.file])


@app.command()
def ls():
    """List all available profiles."""
    print(f"Profiles directory: [b]{config.profiles_dir}[/]")
    print("[b]Profiles:[/]")
    for p in Profile.list_all():
        print(f"* {p.name}")


@app.command()
def rm(
    profile_name: str = typer.Argument(
        ..., help="Profile to remove.", autocompletion=complete_env
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Do not ask any question."),
):
    """Remove profile."""
    profile = Profile(name=profile_name, default=True)
    if force or Confirm.ask(
        f"Do you really want to remove profile [b red]{profile.name}[/]?"
    ):
        profile.file.unlink(missing_ok=True)


@app.command()
def show(
    profile_name: str = typer.Argument(
        ..., help="Profile to display.", autocompletion=complete_profile
    )
):
    """Display profile."""
    profile = Profile(name=profile_name, default=True)
    print(profile.file.read_text())


@app.command(no_args_is_help=True)
def run(
    env_name: str = typer.Argument(
        ..., help="Environment to use.", autocompletion=complete_env
    ),
    profile_name: str = typer.Argument(
        ..., help="Profile to run.", autocompletion=complete_profile
    ),
    force_recreate: bool = typer.Option(False, help="Recreate all containers."),
):
    """Run a profile."""
    env = Env(name=env_name)
    profile = Profile(name=profile_name)

    tmp_dir = Path(tempfile.mkdtemp(prefix="qd-"))
    compose_file = tmp_dir / "compose.yml"
    compose_file.write_text(
        template(
            "compose.yml.j2",
            config=config,
            env=env,
            profile=profile,
        )
    )

    if profile.settings.qontract_schemas_path and env.settings.run_qontract_server:
        make_bundle(
            env.settings.app_interface_path, profile.settings.qontract_server_path
        )

    # stop other qd projects first
    compose_stop_projects(
        ignore=f"qd-{ env.name_path_safe }-{ profile.name_path_safe }"
    )
    print(f"Running containers ({compose_file})")
    compose_up(compose_file, force_recreate=force_recreate)


@app.command(no_args_is_help=True)
def render(
    env_name: str = typer.Argument(
        ..., help="Environment to use.", autocompletion=complete_env
    ),
    profile_name: str = typer.Argument(
        ..., help="Profile to render.", autocompletion=complete_profile
    ),
    output_file: Path = typer.Argument(..., help="Output file name", writable=True),
):
    """Render a profile to file."""
    compose_file = template(
        "compose.yml.j2",
        config=config,
        env=Env(name=env_name),
        profile=Profile(name=profile_name),
    )
    output_file.write_text(compose_file)
    print(f"[b green]{output_file}[/] written")
