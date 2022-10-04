import copy
import os
import sys
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, root_validator, validator
from rich import print

from .config import config
from .utils import yaml


class EnvSettings(BaseModel):
    app_interface_path: Path = Path("~/workspace/app-interface")
    app_interface_state_bucket: str = ""
    app_interface_state_bucket_account: str = ""
    config: Path = Path("~/workspace/qontract-reconcile/config.dev.toml")
    run_qontract_reconcile: bool = True
    run_qontract_server: bool = True
    run_vault: bool = False


class ProfileSettings(BaseModel):
    container_uid: int = os.getuid()
    debugger: str = "debugpy"
    dry_run: bool = True
    gitlab_pr_submitter_queue_url: str = ""
    integration_extra_args: str
    integration_name: str
    log_level: str = "INFO"
    qontract_reconcile_build_image: bool = True
    qontract_reconcile_image: str = "quay.io/app-sre/qontract-reconcile:latest"
    qontract_reconcile_path: Path = Path("~/workspace/qontract-reconcile")
    qontract_server_build_image: bool = True
    qontract_server_image: str = "quay.io/app-sre/qontract-server:latest"
    qontract_server_path: Path = Path("~/workspace/qontract-server")
    qontract_schemas_path: Path = Path("~/workspace/qontract-schemas")
    run_once: int = 1
    sleep_duration_secs: int = 10


class Base(BaseModel):
    name: str
    default: bool = False
    _root: Path

    @validator("name")
    def name_remove_suffix(cls, v) -> str:
        p = Path(v)
        return str(p.parent / p.stem)

    @property
    def file(self) -> Path:
        p = self._root / self.name
        p.parent.mkdir(parents=True, exist_ok=True)
        return p.with_suffix(".yml")

    @classmethod
    def list_all(cls) -> list["Base"]:
        items = []
        for f in [f for f in list(cls._root.glob("**/*")) if f.is_file()]:
            items.append(cls(name=str(f.relative_to(cls._root))))
        return items

    @property
    def name_path_safe(self):
        return self.name.replace("/", "_")

    @property
    def default_settings_as_dict(self) -> dict[str, Any]:
        return {}

    @property
    def settings_as_dict(self) -> dict[str, Any]:
        values = self.default_settings_as_dict
        try:
            values.update(
                **yaml.safe_load(
                    self.file.read_text(encoding=config.__config__.env_file_encoding)
                )
            )
        except FileNotFoundError:
            pass
        return values

    def dump(self):
        values = self.settings.dict(
            exclude_defaults=not self.default, exclude_unset=not self.default
        )

        if not self.default:
            # do not dump settings from defaults
            defaults = self.default_settings_as_dict
            for k in copy.deepcopy(values):
                if k in defaults:
                    del values[k]

        self.file.write_text(
            yaml.dump(
                values,
                explicit_start=True,
                indent=4,
                default_flow_style=False,
            )
        )


class Env(Base):
    _root: Path = config.environments_dir
    settings: Optional[EnvSettings]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.load_settings()

    def load_settings(self):
        values = {"integration_name": "changeme", "integration_extra_args": ""}
        values.update(**self.settings_as_dict)
        self.settings = EnvSettings(**self.settings_as_dict)


class Profile(Base):
    _root: Path = config.profiles_dir
    settings: Optional[ProfileSettings]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.load_settings()

    @root_validator(pre=True)
    def name_not_default(cls, values):
        if values.get("name") == config.defaults_profile and not values.get("default"):
            print(
                "[b red]This profile holds just default variables and isn't supposed to run![/]"
            )
            sys.exit(1)
        return values

    @property
    def default_settings_as_dict(self) -> dict[str, Any]:
        if self.default:
            return {}

        try:
            return yaml.safe_load(
                DEFAULT_PROFILE.file.read_text(
                    encoding=config.__config__.env_file_encoding
                )
            )
        except FileNotFoundError:
            return super().default_settings_as_dict

    def load_settings(self):
        values = {"integration_name": "changeme", "integration_extra_args": ""}
        values.update(**self.settings_as_dict)
        self.settings = ProfileSettings(**values)


DEFAULT_PROFILE = Profile(name=config.defaults_profile, default=True)
