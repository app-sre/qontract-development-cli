from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from tempfile import NamedTemporaryFile


class SkillInstallError(Exception):
    """An installation conflict requiring user action."""


def available_skills() -> list[str]:
    """Discover every bundled skill directory with a SKILL.md resource."""
    return sorted(
        directory.name
        for directory in files("qontract_development_cli").joinpath("skills").iterdir()
        if directory.is_dir() and directory.joinpath("SKILL.md").is_file()
    )


def install(destination: Path, *, skill_name: str) -> Path:
    """Refresh the bundled skill, leaving identical content and unrelated files untouched."""
    target = destination.expanduser().absolute() / skill_name / "SKILL.md"
    if ".." in target.parts or any(
        path.is_symlink() for path in (target, *target.parents)
    ):
        raise SkillInstallError("Refusing symlinks or '..' in the installation path.")
    content = (
        files("qontract_development_cli")
        .joinpath("skills", skill_name, "SKILL.md")
        .read_bytes()
    )
    if target.exists():
        if not target.is_file():
            raise SkillInstallError(f"Not a regular file: {target}")
        if target.read_bytes() == content:
            return target
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
        staged = Path(temporary.name)
        temporary.write(content)
    try:
        staged.replace(target)
    finally:
        staged.unlink(missing_ok=True)
    return target
