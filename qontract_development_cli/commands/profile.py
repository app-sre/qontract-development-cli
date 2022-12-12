import logging
import subprocess
import tempfile
from multiprocessing import Process
from pathlib import Path
from typing import Optional

import typer
from getkey import getkey
from rich.prompt import (
    Confirm,
    Prompt,
)
from rich.table import Table

from qontract_development_cli.watchdog import watch_files

from ..completions import (
    complete_env,
    complete_profile,
)
from ..config import config
from ..models import (
    Env,
    Profile,
)
from ..shell import (
    compose_down,
    compose_log_tail,
    compose_restart,
    compose_stop_project,
    compose_up,
    fetch_pull_requests,
    make_bundle,
    make_bundle_and_restart_server,
)
from ..templates import template
from ..utils import console

app = typer.Typer()
log = logging.getLogger(__name__)


@app.command()
def create(
    profile_name: str = typer.Argument(..., help="Profile to create."),
    integration_name: Optional[str] = typer.Option(None),
    integration_extra_args: Optional[str] = typer.Option(None),
    app_interface: Optional[Path] = typer.Option(
        None,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        exists=True,
        help="Path to local app-interface instance git working copy.",
    ),
    app_interface_pr: Optional[int] = typer.Option(None, help="PR/MR to use"),
    app_interface_upstream: str = typer.Option("upstream", help="Upstream remote name"),
    qontract_schemas: Optional[Path] = typer.Option(
        None,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        exists=True,
        help="Path to local qontract-schemas git working copy.",
    ),
    qontract_schemas_pr: Optional[int] = typer.Option(None, help="PR/MR to use"),
    qontract_schemas_upstream: str = typer.Option(
        "upstream", help="Upstream remote name"
    ),
    qontract_reconcile: Optional[Path] = typer.Option(
        None,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        exists=True,
        help="Path to local qontract-reconcile git working copy.",
    ),
    qontract_reconcile_pr: Optional[int] = typer.Option(None, help="PR/MR to use"),
    qontract_reconcile_upstream: str = typer.Option(
        "upstream", help="Upstream remote name"
    ),
):
    """Create a new profile to run an integration."""
    if profile_name in [p.name for p in Profile.list_all()]:
        console.print(
            f"[b red]Profile {profile_name} already exists![/] Choose another profile name."
        )
        raise typer.Exit(1)
    profile = Profile(name=profile_name)
    if integration_name is None:
        profile.settings.integration_name = Prompt.ask(
            "Integration name", console=console, default=profile_name
        )
    else:
        profile.settings.integration_name = integration_name
    if integration_extra_args is None:
        profile.settings.integration_extra_args = Prompt.ask(
            "Integration extra arguments", default="", console=console
        )
    else:
        profile.settings.integration_extra_args = integration_extra_args

    if app_interface:
        profile.settings.app_interface_path = app_interface
    if app_interface_pr:
        profile.settings.app_interface_pr = app_interface_pr
    profile.settings.app_interface_upstream = app_interface_upstream

    if qontract_schemas:
        profile.settings.qontract_schemas_path = qontract_schemas
    if qontract_schemas_pr:
        profile.settings.qontract_schemas_pr = qontract_schemas_pr
    profile.settings.qontract_schemas_upstream = qontract_schemas_upstream

    if qontract_reconcile:
        profile.settings.qontract_reconcile_path = qontract_reconcile
    if qontract_reconcile_pr:
        profile.settings.qontract_reconcile_pr = qontract_reconcile_pr
    profile.settings.qontract_reconcile_upstream = qontract_reconcile_upstream
    profile.dump()
    console.print(f"Profile [green]{profile.name}[/] created!")


@app.command()
def edit(
    profile_name: str = typer.Argument(
        ..., help="Profile to edit.", autocompletion=complete_profile
    )
):
    """Edit a profile in your editor."""
    profile = Profile(name=profile_name)
    console.print(f"Opening [b]{profile.name}[/] in your editor ...")
    subprocess.run([config.editor, profile.file])


@app.command()
def ls():
    """List all available profiles."""
    console.print(f"Profiles directory: [b]{config.profiles_dir}[/]")
    console.print("[b]Profiles:[/]")
    for p in Profile.list_all():
        console.print(f"* {p.name}")


@app.command()
def rm(
    profile_name: str = typer.Argument(
        ..., help="Profile to remove.", autocompletion=complete_profile
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Do not ask any question."),
):
    """Remove profile."""
    profile = Profile(name=profile_name)
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
    profile = Profile(name=profile_name)
    console.print(profile.file.read_text())


@app.command(no_args_is_help=True)
def run(
    env_name: str = typer.Argument(
        ..., help="Environment to use.", autocompletion=complete_env
    ),
    profile_name: str = typer.Argument(
        ..., help="Profile to run.", autocompletion=complete_profile
    ),
    force_recreate: bool = typer.Option(False, help="Recreate all containers."),
    force_build: bool = typer.Option(False, help="Rebuild all containers."),
    qontract_reconcile_monitor_file_changes: bool = typer.Option(
        True,
        help="Restart integration when files changed in qontract-reconcile path",
    ),
    qontract_reconcile_monitor_file_extensions: str = typer.Option(
        ".py .pyx .pyd",
        help="Monitor these file extensions",
    ),
    qontract_schemas_monitor_file_changes: bool = typer.Option(
        True,
        help="Rebuild bundle and restart qontract-server when files changed in qontract-schemas path",
    ),
    qontract_schemas_monitor_file_extensions: str = typer.Option(
        ".json .yml .yaml",
        help="Monitor these file extensions",
    ),
):
    """Run a profile."""
    env = Env(name=env_name)
    profile = Profile(name=profile_name)
    profile.settings.app_interface_path = (
        profile.settings.app_interface_path or env.settings.app_interface_path
    )
    # prepare worktrees
    fetch_pull_requests(profile, config.worktrees_dir)

    # settings
    settings = Table("Item", "Path", title="Settings")
    settings.add_row(
        "APP Interface", f"[green] {profile.settings.app_interface_path} [/]"
    )
    settings.add_row("Schemas", f"[green] {profile.settings.qontract_schemas_path} [/]")
    settings.add_row(
        "Reconcile", f"[green] {profile.settings.qontract_reconcile_path} [/]"
    )
    console.print(settings)

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

    if env.settings.run_qontract_server:
        make_bundle(
            profile.settings.app_interface_path, profile.settings.qontract_server_path
        )

    # stop other qontract-development project first
    compose_stop_project(config.docker_compose_project_name)
    console.print(f"Running containers ({compose_file})")
    compose_up(compose_file, force_recreate=force_recreate, build=force_build)
    log_tail_proc = compose_log_tail(compose_file)
    shortcuts_info = Table("Key", "Description", title="Shortcuts")
    shortcuts_info.add_row("r", "Restart qontract-reconcile container")
    shortcuts_info.add_row("b", "Make bundle and restart qontract-server container")
    shortcuts_info.add_row("q", "Quit")
    console.print(shortcuts_info)

    file_watchers: list[Process] = []
    if qontract_reconcile_monitor_file_changes:
        file_watchers.append(
            watch_files(
                path=profile.settings.qontract_reconcile_path.expanduser().absolute(),
                extensions=qontract_reconcile_monitor_file_extensions.split(" "),
                action=compose_restart,
                action_args=(compose_file, "qontract-reconcile"),
            ),
        )
    if qontract_schemas_monitor_file_changes:
        file_watchers.append(
            watch_files(
                path=profile.settings.qontract_schemas_path.expanduser().absolute(),
                extensions=qontract_schemas_monitor_file_extensions.split(" "),
                action=make_bundle_and_restart_server,
                action_args=(
                    profile.settings.app_interface_path,
                    profile.settings.qontract_server_path,
                    compose_file,
                ),
            ),
        )

    while True:
        try:
            key = getkey()
        except KeyboardInterrupt:
            key = "q"

        if key.lower() == "r":
            compose_restart(compose_file, "qontract-reconcile")
        elif key.lower() == "b":
            if not env.settings.run_qontract_server:
                console.print(
                    "[b red]Enable 'run_qontract_server' in your environment settings first![/]"
                )
                continue
            make_bundle_and_restart_server(
                profile.settings.app_interface_path,
                profile.settings.qontract_server_path,
                compose_file,
            )
        elif key.lower() == "q":
            for p in file_watchers:
                p.kill()
            log_tail_proc.kill()
            compose_down(compose_file)
            raise typer.Exit(0)
        else:
            console.print(shortcuts_info)
