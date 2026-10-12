from __future__ import annotations

from typing import TYPE_CHECKING

from .config import get_config
from .models import Env, Profile
from .process import SetupError
from .shell import fetch_pull_requests, make_bundle
from .templates import template

if TYPE_CHECKING:
    from pathlib import Path

    from .process import Runner


def resolve_run(
    env_name: str, profile_name: str, *, require_files: bool = False
) -> tuple[Env, Profile]:
    """Resolve existing environment/default/profile precedence without saving files."""
    if require_files:
        for directory, name in (
            (get_config().environments_dir, env_name),
            (get_config().profiles_dir, profile_name),
        ):
            if not (directory / name).with_suffix(".yml").is_file():
                raise SetupError(f"Missing saved environment/profile: {name}")
    env = Env(name=env_name)
    profile = Profile(name=profile_name)
    profile.settings.app_interface_path = (
        profile.settings.app_interface_path or env.settings.app_interface_path
    )
    return env, profile


def prepare_run(
    env: Env,
    profile: Profile,
    directory: Path,
    *,
    headless: bool = False,
    runner: Runner | None = None,
) -> Path:
    """Prepare worktrees, bundle, and the same Compose stack for either run mode."""
    fetch_pull_requests(profile, get_config().worktrees_dir, runner=runner)
    if (
        env.settings.run_qontract_server
        and not profile.settings.skip_initial_make_bundle
    ):
        if profile.settings.app_interface_path is None:
            raise SetupError("Missing app-interface path")
        make_bundle(
            profile.settings.app_interface_path,
            profile.settings.qontract_server_path,
            runner=runner,
        )
    return render_compose(env, profile, directory, headless=headless)


def render_compose(
    env: Env,
    profile: Profile,
    directory: Path,
    *,
    headless: bool = False,
) -> Path:
    """Render the same packaged service and override templates for both modes."""
    services = profile.settings.compose_template_files(
        api=env.settings.run_qontract_api,
        cache=env.settings.run_cache,
        opa=env.settings.run_opa,
        reconcile=env.settings.run_qontract_reconcile,
        server=env.settings.run_qontract_server,
        subscriber=env.settings.run_qontract_api_subscriber,
        vault=env.settings.run_vault,
        worker=env.settings.run_qontract_api_worker,
    )
    for filename in ("compose.yml.j2", "compose.override.yml.j2", *services):
        (directory / filename.removesuffix(".j2")).write_text(
            template(
                filename,
                config=get_config(),
                env=env,
                profile=profile,
                compose_files=[name.removesuffix(".j2") for name in services],
                headless=headless,
            )
        )
    return directory / "compose.yml"
