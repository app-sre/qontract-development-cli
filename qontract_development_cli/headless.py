from __future__ import annotations

import math
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from .orchestration import prepare_run, resolve_run
from .process import (
    RunInterruptedError,
    Runner,
    RunTimeoutError,
    SetupError,
    handle_signals,
)
from .report import Execution, Outcome, RunReport
from .shell import compose_command

CLEANUP_SECONDS = 15
SETUP_EXIT = 125
TIMEOUT_EXIT = 124
CLEANUP_EXIT = 126


class RunOptions(BaseModel, frozen=True):
    env_name: str
    profile_name: str
    output_dir: Path
    timeout: float = 600
    no_dry_run: bool = False
    force_build: bool = False
    force_recreate: bool = False
    skip_initial_make_bundle: bool | None = None


def run_headless(options: RunOptions) -> int:
    """Run the normal Compose stack once, retain logs, and tear it all down."""
    started = datetime.now(tz=UTC)
    try:
        output = _output_directory(options.output_dir)
    except (OSError, SetupError) as error:
        sys.stderr.write(f"Cannot prepare output directory: {error}\n")
        return SETUP_EXIT

    runner = Runner(
        deadline=time.monotonic() + options.timeout, setup_log=output / "setup.log"
    )
    execution = _execute(options, runner)
    report = RunReport(
        environment=options.env_name,
        profile=options.profile_name,
        started_at=started,
        ended_at=datetime.now(tz=UTC),
        timeout_seconds=options.timeout,
        execution=execution,
        setup_log=output / "setup.log",
        integration_log=output / "integration.log",
        stack_log=output / "stack.log",
    )
    report.write(output / "result.json")
    summary = f"Execution: {execution.outcome}; exit {execution.exit_code}. Report: {output / 'result.json'}"
    runner.note(summary)
    return execution.exit_code


def _execute(options: RunOptions, runner: Runner) -> Execution:
    try:
        with handle_signals(), tempfile.TemporaryDirectory(prefix="qd-") as directory:
            return _prepare_and_run(Path(directory), runner=runner, options=options)
    except (
        RunInterruptedError,
        RunTimeoutError,
        SetupError,
        OSError,
        ValidationError,
        YAMLError,
    ) as error:
        return _failure(error)


def _prepare_and_run(
    directory: Path, *, runner: Runner, options: RunOptions
) -> Execution:
    if options.no_dry_run:
        raise SetupError("--headless rejects --no-dry-run")
    if not math.isfinite(options.timeout) or options.timeout <= 0:
        raise SetupError("Headless timeout must be positive and finite")
    env, profile = resolve_run(
        options.env_name, options.profile_name, require_files=True
    )
    if not env.settings.run_qontract_reconcile:
        raise SetupError("Headless requires run_qontract_reconcile: true")
    profile.settings.dry_run = True
    profile.settings.debugger = ""
    profile.settings.run_once = True
    if options.skip_initial_make_bundle is not None:
        profile.settings.skip_initial_make_bundle = options.skip_initial_make_bundle
    compose_file = prepare_run(env, profile, directory, headless=True, runner=runner)
    return _run_stack(compose_file, runner=runner, options=options)


def _run_stack(compose_file: Path, *, runner: Runner, options: RunOptions) -> Execution:
    try:
        execution = _start_and_run(compose_file, runner=runner, options=options)
    except (RunInterruptedError, RunTimeoutError, SetupError, OSError) as error:
        execution = _failure(error)
    finally:
        cleanup_completed, cleanup_errors = _cleanup(compose_file, runner)
    return Execution(
        outcome=Outcome.CLEANUP_FAILURE
        if execution.exit_code == 0 and cleanup_errors
        else execution.outcome,
        exit_code=CLEANUP_EXIT
        if execution.exit_code == 0 and cleanup_errors
        else execution.exit_code,
        integration_exit_code=execution.integration_exit_code,
        signal=execution.signal,
        cleanup_completed=cleanup_completed,
        errors=[*execution.errors, *cleanup_errors],
    )


def _start_and_run(
    compose_file: Path, *, runner: Runner, options: RunOptions
) -> Execution:
    compose = compose_command(compose_file, plain=True)
    runner.note("Starting the full Compose stack")
    runner.run([*compose, "down", "--remove-orphans", "--timeout", "1"])
    if options.force_build:
        runner.run([*compose, "build"])
    runner.run([
        *compose,
        "up",
        "--wait",
        "--wait-timeout",
        str(math.ceil(runner.remaining())),
        "--no-build",
        "--pull",
        "missing",
        "--remove-orphans",
        "--scale",
        "qontract-reconcile=0",
        *(["--force-recreate"] if options.force_recreate else []),
    ])
    runner.note("Running the integration")
    code = runner.run(
        [
            *compose,
            "run",
            "--rm",
            "--no-deps",
            "-T",
            "--interactive=false",
            "--pull",
            "never",
            "qontract-reconcile",
        ],
        destination=runner.setup_log.parent / "integration.log",
        check=False,
    )
    return Execution(
        outcome=Outcome.SUCCESS if code == 0 else Outcome.INTEGRATION_FAILURE,
        exit_code=code,
        integration_exit_code=code,
    )


def _cleanup(compose_file: Path, runner: Runner) -> tuple[bool, list[str]]:
    compose = compose_command(compose_file, plain=True)
    errors: list[str] = []
    completed = False
    with handle_signals(ignore=True):
        runner.deadline = time.monotonic() + 5
        try:
            runner.run(
                [*compose, "logs", "--no-color", "--timestamps"],
                destination=runner.setup_log.parent / "stack.log",
            )
        except (RunTimeoutError, SetupError, OSError) as error:
            errors.append(f"Log collection failed: {error}")
        runner.deadline = time.monotonic() + CLEANUP_SECONDS - 5
        try:
            runner.run([*compose, "down", "--remove-orphans", "--timeout", "1"])
            completed = True
        except (RunTimeoutError, SetupError, OSError) as error:
            errors.append(f"Stack cleanup failed: {error}")
    return completed, errors


def _failure(error: Exception) -> Execution:
    match error:
        case RunInterruptedError():
            return Execution(
                outcome=Outcome.INTERRUPTED,
                exit_code=128 + error.signum,
                signal=error.signum,
                errors=[str(error)],
            )
        case RunTimeoutError():
            return Execution(
                outcome=Outcome.TIMEOUT, exit_code=TIMEOUT_EXIT, errors=[str(error)]
            )
        case ValidationError() | YAMLError():
            message = "Invalid qd settings; inspect the environment/profile YAML"
        case _:
            message = str(error)
    return Execution(
        outcome=Outcome.SETUP_FAILURE, exit_code=SETUP_EXIT, errors=[message]
    )


def _output_directory(directory: Path) -> Path:
    directory = directory.expanduser().absolute()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if any(directory.iterdir()):
        raise SetupError("Use a new or empty --output-dir")
    for name in ("setup.log", "integration.log", "stack.log"):
        (directory / name).touch(mode=0o600)
    return directory
