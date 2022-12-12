import copy
import os
from pathlib import Path
from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    validator,
)

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
    app_interface_path: Optional[Path] = None
    app_interface_pr: Optional[int] = None
    app_interface_upstream: str = "upstream"
    qontract_reconcile_build_image: bool = True
    qontract_reconcile_image: str = "quay.io/app-sre/qontract-reconcile:latest"
    qontract_reconcile_path: Path = Path("~/workspace/qontract-reconcile")
    qontract_reconcile_pr: Optional[int] = None
    qontract_reconcile_upstream: str = "upstream"
    qontract_server_build_image: bool = True
    qontract_server_image: str = "quay.io/app-sre/qontract-server:latest"
    qontract_server_path: Path = Path("~/workspace/qontract-server")
    qontract_schemas_path: Path = Path("~/workspace/qontract-schemas")
    qontract_schemas_pr: Optional[int] = None
    qontract_schemas_upstream: str = "upstream"
    run_once: bool = True
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
        values = self.settings.dict(  # type: ignore
            exclude_defaults=not self.default, exclude_unset=not self.default
        )
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
    default: bool = True
    settings: EnvSettings

    def __init__(self, *args, **kwargs) -> None:
        if "settings" not in kwargs:
            kwargs["settings"] = EnvSettings()
        super().__init__(*args, **kwargs)
        self.settings = EnvSettings(**self.settings_as_dict)

    def load_settings(self):
        self.settings = EnvSettings(**self.settings_as_dict)


class Profile(Base):
    _root: Path = config.profiles_dir
    settings: ProfileSettings

    def __init__(self, *args, **kwargs) -> None:
        if "settings" not in kwargs:
            kwargs["settings"] = ProfileSettings(**self.default_settings_as_dict)
        super().__init__(*args, **kwargs)
        self.settings = ProfileSettings(**self.settings_as_dict)

    @property
    def default_settings_as_dict(self) -> dict[str, Any]:
        defaults = {"integration_name": "changeme", "integration_extra_args": ""}
        try:
            defaults.update(
                yaml.safe_load(
                    DEFAULT_PROFILE.file.read_text(
                        encoding=config.__config__.env_file_encoding
                    )
                )
            )
        except (FileNotFoundError, AttributeError, NameError):
            pass
        return defaults

    def dump(self):
        values = self.settings.dict(
            exclude_defaults=not self.default, exclude_unset=not self.default
        )

        if not self.default:
            # do not dump settings from defaults
            for k in copy.deepcopy(values):
                if getattr(DEFAULT_PROFILE.settings, k, None) == values[k]:
                    del values[k]

        self.file.write_text(
            yaml.dump(
                values,
                explicit_start=True,
                indent=4,
                default_flow_style=False,
            )
        )


DEFAULT_PROFILE = Profile(name=config.defaults_profile, default=True)
