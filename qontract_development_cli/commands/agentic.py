from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ..skill import SkillInstallError, available_skills
from ..skill import install as install_skill

app = typer.Typer()


@app.command()
def skill_install(
    *,
    destination: Annotated[
        Path | None,
        typer.Option(help="Manual skills directory instead of the standard locations."),
    ] = None,
) -> None:
    """Install or update all bundled agent skills without Docker or profiles."""
    destinations = (
        [destination]
        if destination is not None
        else [Path.home() / ".agents" / "skills"]
    )
    claude = Path.home() / ".claude" / "skills"
    if destination is None and claude.exists():
        destinations.append(claude)
    skills = available_skills()
    for directory in destinations:
        for skill_name in skills:
            try:
                installed = install_skill(directory, skill_name=skill_name)
            except (SkillInstallError, OSError) as error:
                typer.echo(
                    f"Cannot install skill: {error}. Check the destination and its permissions.",
                    err=True,
                )
                raise typer.Exit(1) from error
            typer.echo(str(installed))
