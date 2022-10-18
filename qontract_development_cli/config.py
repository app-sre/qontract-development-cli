import os
import platform
from pathlib import Path
from typing import Any

from appdirs import AppDirs  # type: ignore
from pydantic import BaseSettings

from .utils import yaml

appdirs = AppDirs("qontract-development", "appsre")

user_config_dir = Path(appdirs.user_config_dir)
user_config_dir.mkdir(parents=True, exist_ok=True)
user_config_file = user_config_dir / "config.yaml"

user_cache_dir = Path(appdirs.user_cache_dir)
user_cache_dir.mkdir(parents=True, exist_ok=True)

is_mac = platform.system().lower() == "darwin"


def yaml_config_settings_source(settings: BaseSettings) -> dict[str, Any]:
    encoding = settings.__config__.env_file_encoding
    if user_config_file.exists():
        cfg = yaml.safe_load(user_config_file.read_text(encoding))
        return cfg if cfg else {}
    return {}


class Config(BaseSettings):
    debug: bool = False
    defaults_profile: str = "defaults"
    docker_compose_project_name: str = "qontract-development"
    editor: str = os.environ.get("EDITOR", "vim")
    environments_dir: Path = user_config_dir / "environments"
    profiles_dir: Path = user_config_dir / "profiles"
    worktrees_dir: Path = user_cache_dir / "worktrees"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.environments_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    class Config:
        extra = "ignore"
        env_file_encoding = "utf-8"
        env_prefix = "qontract_development_"

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (init_settings, env_settings, yaml_config_settings_source)

    def save(self):
        user_config_file.write_text(
            yaml.dump(
                self.dict(),
                explicit_start=True,
                indent=4,
                default_flow_style=False,
            ),
            encoding=self.__config__.env_file_encoding,
        )


config = Config()
