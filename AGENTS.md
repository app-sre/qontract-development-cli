# Repository instructions

## Development commands

- Requires Python **3.14+** and `uv`; install development dependencies with
  `uv sync --frozen`. Use `uv run --frozen` for repo-local commands, not an
  independently installed `qd`.
- `make test` is the full CI check, in order: `qd --version`, Ruff lint without
  fixes, Ruff format check, mypy, pytest. `make format` runs Ruff fixes first,
  then formats; `ruff check` also modifies files by default (`fix = true`).
- Focused tests: `uv run --frozen pytest tests/test_reconcile_template.py`;
  add `-k test_additional_environment_with_colon_produces_valid_yaml` for one test.
  These tests render templates and parse YAML; Docker and sibling repositories
  are not required.
- `uv run --frozen mypy` is strict and checks `qontract_development_cli`, with the Pydantic
  plugin. Preserve Ruff's runtime-evaluated Pydantic/Typer configuration when
  changing imports or annotations.
- CI lives in `.tekton/`, not GitHub Actions: PRs build Docker's `test` stage
  (`uv lock --locked`, `uv sync --frozen`, `make test`). Pushes to `main` build the
  `pypi` stage and publish. `make pypi` is a release operation, not a local check.

## Execution and configuration

- `qd` resolves through `__main__.py` to the Typer app in `cli.py`.
  `commands/profile.py:run` prepares PR worktrees, renders Compose files into a
  temporary directory, builds the bundle, starts containers, and launches file
  watchers. Subprocess operations are in `shell.py`; container definitions are
  packaged Jinja templates in `qontract_development_cli/templates/`.
  `orchestration.py` shares resolution/rendering across modes; `headless.py`
  owns the bounded Compose lifecycle, `report.py` owns reporting, and `process.py`
  owns subprocess redirection.
- Compose uses `compose.yml.j2` to include service files and
  `compose.override.yml.j2` for cross-service networking, dependencies, and
  environment overrides. Changes to service wiring may require both templates.
- Configuration is outside the checkout: `config.py` uses
  `AppDirs("qontract-development", "appsre")` and lazily reads `config.yaml` through
  cached `get_config()`. Environment variables prefixed `QONTRACT_DEVELOPMENT_`
  override YAML; `.env` is not loaded. Set overrides before the first load; tests
  changing them must clear `get_config.cache_clear()`. Reading settings does not
  create directories; defaults are read through `get_default_profile()`.
- Profiles overlay the configured defaults profile (normally `defaults.yml`)
  and omit inherited/default values when saved. Use `models.py` as the source of
  truth for settings; README defaults can lag behind it. When constructing
  `ProfileSettings` directly, supply `localstack_compose_file=None` to let its
  validator derive the path; the nullable field has no default.
- In `reconcile.yml.j2`, keep arbitrary command arguments and additional
  environment entries quoted with `tojson`. The template tests verify that
  colon-space and `#` remain literal values rather than YAML syntax.

## Runtime cautions

- Running an interactive profile requires Docker Compose with `include` support and configured
  sibling checkouts. It is not a unit-test shortcut: even with `dry_run: true`,
  it can build images/bundles, fetch PRs/create worktrees, and stop an existing
  Compose project with the configured name (default `qontract-development`).
- `--no-dry-run` overrides the profile's dry-run setting. PR worktrees default
  to remote `upstream` and are not automatically cleaned up. Bundle rebuilds run
  `make -C <qontract_server_path> bundle` with `APP_INTERFACE_PATH` set; both modes
  stop on a nonzero bundle-build exit.
  Explicit `--skip-initial-make-bundle` / `--no-skip-initial-make-bundle` flags
  override the saved setting in memory only; an omitted flag inherits it.
- Headless mode selects dry-run/run-once defaults and rejects `--no-dry-run`.
  `additional_environment` intentionally permits overriding generated runtime settings;
  preserve these user overrides rather than treating them as a bug. Keep the
  existing inverse `--no-no-dry-run`; there is no new `--dry-run` qd option.
  Never route headless completion through `getkey()` or remove volumes.
  Both modes prepare the same worktrees/bundle/Compose project. Headless replaces
  the existing stack, starts all configured supporting services with `up --wait`,
  runs reconcile in the foreground, collects logs, and tears down the whole stack
  on every exit. Service readiness belongs in Compose health checks, not Python
  application probes or per-container lifecycle code.
- Reuse existing images by default. `--force-rebuild` (existing `--force-build`
  alias retained) requests a cached rebuild. The agent checks dependency-manifest
  changes and requests a rebuild once, not for every integration.
- The headless success path was manually verified with `automated-actions-config`.
  Unit tests now cover the Compose lifecycle, failure/timeout/interrupt cleanup,
  subprocess output, service templates, and interactive output isolation.
  Mock external Compose operations at the subprocess boundary; do not recreate
  Docker or application internals in a fake lifecycle. Unit tests do not replace
  real integration validation or authorize production-configured reruns.
- `qd agentic skill-install` copies packaged resources to `~/.agents/skills` and
  existing `~/.claude/skills`; `--destination` replaces those targets. Do not add
  tool detection or load user profiles during installation.
- Bundled skills live under `qontract_development_cli/skills/`; directories with
  `SKILL.md` are discovered automatically. Setup guidance must not blindly rerun
  `config init`, which writes global config, `dev.yml`, and defaults.
- Skill installation always refreshes differing bundled content; identical
  files are untouched. There is no `--replace` option.
