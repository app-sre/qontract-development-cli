import os
import platform
from pathlib import Path

from appdirs import AppDirs
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .utils import yaml

appdirs = AppDirs("qontract-development", "appsre")

user_config_dir = Path(appdirs.user_config_dir)
user_config_dir.mkdir(parents=True, exist_ok=True)
user_config_file = user_config_dir / "config.yaml"

user_cache_dir = Path(appdirs.user_cache_dir)
user_cache_dir.mkdir(parents=True, exist_ok=True)

is_mac = platform.system().lower() == "darwin"


class Config(BaseSettings):
    debug: bool = False
    defaults_profile: str = "defaults"
    docker_compose_project_name: str = "qontract-development"
    editor: str = os.environ.get("EDITOR", "vim")
    environments_dir: Path = user_config_dir / "environments"
    profiles_dir: Path = user_config_dir / "profiles"
    worktrees_dir: Path = user_cache_dir / "worktrees"

    def __init__(self) -> None:
        super().__init__()
        self.environments_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
        )

    model_config = SettingsConfigDict(
        yaml_file=user_config_file,
        yaml_file_encoding="utf-8",
        env_prefix="qontract_development_",
    )

    def save(self) -> None:
        user_config_file.write_text(
            yaml.dump(
                self.model_dump(),
                explicit_start=True,
                indent=4,
                default_flow_style=False,
            ),
            encoding=self.model_config["yaml_file_encoding"],
        )


config = Config()
