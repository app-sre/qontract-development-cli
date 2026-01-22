import contextlib
import copy
import os
from pathlib import Path
from typing import Any, ClassVar, Self

from pydantic import BaseModel, model_validator

from .config import config
from .utils import yaml


class EnvSettings(BaseModel):
    app_interface_path: Path = Path("~/workspace/app-interface")
    app_interface_state_bucket: str = ""
    app_interface_state_bucket_account: str = ""
    config: Path = Path("~/workspace/qontract-reconcile/config.dev.toml")
    container_platform: str = "linux/amd64"
    gitlab_pr_submitter_queue_url: str = ""
    run_qontract_api: bool = False
    run_qontract_api_worker: bool = False
    run_cache: bool = False
    run_qontract_reconcile: bool = True
    run_qontract_server: bool = True
    run_vault: bool = False


class ProfileSettings(BaseModel):
    command: str = "run-integration"
    command_extra_args: str = ""
    container_uid: int = os.getuid()
    debugger: str = "debugpy"
    dry_run: bool = True
    integration_extra_args: str | int = ""
    integration_name: str = ""
    log_level: str = "INFO"
    app_interface_path: Path | None = None
    app_interface_pr: int | None = None
    app_interface_upstream: str = "upstream"
    extra_hosts: list[str] = []
    run_once: bool = True
    sleep_duration_secs: int = 10
    additional_environment: dict[str, Any] = {}
    skip_initial_make_bundle: bool = False

    # api
    qontract_api_build_image: bool = True
    qontract_api_image: str = "quay.io/redhat-services-prod/app-sre-tenant/qontract-reconcile-master/qontract-api-master:latest"
    qontract_api_container_platform: str | None = None
    qontract_api_compose_file: str = "api.yml.j2"
    qontract_api_debugger_port: int = 5679

    # api-worker
    qontract_api_worker_build_image: bool = True
    qontract_api_worker_image: str = "quay.io/redhat-services-prod/app-sre-tenant/qontract-reconcile-master/qontract-api-worker-master:latest"
    qontract_api_worker_container_platform: str | None = None
    qontract_api_worker_compose_file: str = "worker.yml.j2"
    qontract_api_worker_debugger_port: int = 5680

    # cache
    cache_image: str = "redis:7-alpine"
    cache_container_platform: str | None = None
    cache_compose_file: str = "cache.yml.j2"

    # reconcile
    qontract_reconcile_build_image: bool = True
    qontract_reconcile_image: str = "quay.io/redhat-services-prod/app-sre-tenant/qontract-reconcile-master/qontract-reconcile-master:latest"
    qontract_reconcile_container_platform: str | None = None
    qontract_reconcile_path: Path = Path("~/workspace/qontract-reconcile")
    qontract_reconcile_pr: int | None = None
    qontract_reconcile_upstream: str = "upstream"
    qontract_reconcile_compose_file: str = "reconcile.yml.j2"
    qontract_reconcile_debugger_port: int = 5678

    # server
    qontract_server_build_image: bool = True
    qontract_server_image: str = "quay.io/redhat-services-prod/app-sre-tenant/qontract-server-master/qontract-server-master:latest"
    qontract_server_container_platform: str | None = None
    qontract_server_path: Path = Path("~/workspace/qontract-server")
    qontract_server_compose_file: str = "server.yml.j2"
    qontract_server_debugger_port: int = 6789

    # schemas
    qontract_schemas_path: Path = Path("~/workspace/qontract-schemas")
    qontract_schemas_pr: int | None = None
    qontract_schemas_upstream: str = "upstream"

    # internal redhat ca
    internal_redhat_ca: bool = False
    internal_redhat_ca_image: str = "quay.io/redhat-services-prod/app-sre-tenant/container-images-int-master/internal-redhat-ca-master:latest"
    internal_redhat_ca_container_platform: str | None = None
    internal_redhat_ca_compose_file: str = "internal-redhat-ca.yml.j2"

    # localstack
    localstack: bool = False
    localstack_compose_file: Path | None

    # vault
    vault_image: str = "vault:1.5.4"
    vault_container_platform: str | None = None
    vault_compose_file: str = "vault.yml.j2"

    @model_validator(mode="after")
    def default_localstack_compose_file(self) -> Self:
        self.localstack_compose_file = (
            self.localstack_compose_file
            or self.qontract_reconcile_path / "dev/localstack/docker-compose.yml"
        )
        return self

    @property
    def qontract_api_path(self) -> Path | None:
        return self.qontract_reconcile_path / "qontract_api"

    def compose_template_files(  # noqa: PLR0913
        self,
        *,
        api: bool,
        cache: bool,
        reconcile: bool,
        server: bool,
        vault: bool,
        worker: bool,
    ) -> list[str]:
        files = [self.qontract_api_compose_file] if api else []
        files += [self.qontract_api_worker_compose_file] if worker else []
        files += [self.cache_compose_file] if cache else []
        files += [self.qontract_reconcile_compose_file] if reconcile else []
        files += [self.qontract_server_compose_file] if server else []
        files += [self.vault_compose_file] if vault else []
        files += (
            [self.internal_redhat_ca_compose_file] if self.internal_redhat_ca else []
        )
        return files


class Base(BaseModel):
    name: str
    default: bool = False
    root: ClassVar[Path]

    def __lt__(self, other: "Base") -> bool:
        return self.name < other.name

    @model_validator(mode="after")
    def name_remove_suffix(self) -> Self:
        p = Path(self.name)
        self.name = str(p.parent / p.stem)
        return self

    @property
    def file(self) -> Path:
        p = self.root / self.name
        p.parent.mkdir(parents=True, exist_ok=True)
        return p.with_suffix(".yml")

    @classmethod
    def list_all(cls) -> list["Base"]:
        items = []
        for f in [f for f in list(cls.root.glob("**/*")) if f.is_file()]:
            items.append(  # noqa: PERF401
                cls(name=str(f.relative_to(cls.root)))
            )
        return items

    @property
    def name_path_safe(self) -> str:
        return self.name.replace("/", "_")

    @property
    def default_settings_as_dict(self) -> dict[str, Any]:
        return {}

    @property
    def settings_as_dict(self) -> dict[str, Any]:
        values = self.default_settings_as_dict
        with contextlib.suppress(FileNotFoundError):
            values.update(
                **yaml.safe_load(
                    self.file.read_text(
                        encoding=config.model_config["yaml_file_encoding"]
                    )
                )
            )
        return values

    def dump(self) -> None:
        values = self.settings.dict(  # type: ignore[attr-defined]
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
    root: ClassVar[Path] = config.environments_dir
    default: bool = True
    settings: EnvSettings

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "settings" not in kwargs:
            kwargs["settings"] = EnvSettings()
        super().__init__(*args, **kwargs)
        self.settings = EnvSettings(**self.settings_as_dict)

    def load_settings(self) -> None:
        self.settings = EnvSettings(**self.settings_as_dict)


class Profile(Base):
    root: ClassVar[Path] = config.profiles_dir
    settings: ProfileSettings

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "settings" not in kwargs:
            kwargs["settings"] = ProfileSettings(**self.default_settings_as_dict)
        super().__init__(*args, **kwargs)
        self.settings = ProfileSettings(**self.settings_as_dict)

    @property
    def default_settings_as_dict(self) -> dict[str, Any]:
        defaults = {
            "integration_name": "changeme",
            "integration_extra_args": "",
            "localstack_compose_file": None,
        }
        with contextlib.suppress(FileNotFoundError, AttributeError, NameError):
            defaults.update(
                yaml.safe_load(
                    DEFAULT_PROFILE.file.read_text(
                        encoding=config.model_config["yaml_file_encoding"]
                    )
                )
            )

        return defaults

    def dump(self) -> None:
        values = self.settings.model_dump(
            mode="json",
            exclude_defaults=not self.default,
            exclude_unset=not self.default,
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
