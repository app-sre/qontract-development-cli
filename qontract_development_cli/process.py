from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from pathlib import Path
    from types import FrameType


class SetupError(Exception):
    """A prerequisite or setup command failed."""


class RunTimeoutError(Exception):
    """The whole-run deadline expired."""


class RunInterruptedError(Exception):
    """A termination signal interrupted the invocation."""

    def __init__(self, signum: int, *, location: str) -> None:
        self.signum = signum
        super().__init__(f"Received {signal.Signals(signum).name} during {location}")


class Runner:
    """Run bounded subprocesses with complete stdout/stderr redirected to disk."""

    def __init__(self, *, deadline: float, setup_log: Path) -> None:
        self.deadline = deadline
        self.setup_log = setup_log

    def remaining(self) -> float:
        """Return the remaining whole-run budget."""
        if (remaining := self.deadline - time.monotonic()) <= 0:
            raise RunTimeoutError("Whole-run deadline exceeded")
        return remaining

    def note(self, message: str) -> None:
        """Append a short lifecycle message to the setup log."""
        with self.setup_log.open("a", encoding="utf-8") as stream:
            stream.write(message + "\n")
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def run(
        self,
        args: Sequence[str],
        *,
        destination: Path | None = None,
        check: bool = True,
    ) -> int:
        """Run without stdin, preserving combined output and the actual exit code."""
        self.remaining()
        with (destination or self.setup_log).open("ab") as output:
            process = subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env={
                    **os.environ,
                    "NO_COLOR": "1",
                    "TERM": "dumb",
                    "GIT_TERMINAL_PROMPT": "0",
                },
            )
            try:
                code = process.wait(timeout=self.remaining())
            except BaseException as error:
                _terminate(process)
                if isinstance(error, subprocess.TimeoutExpired):
                    raise RunTimeoutError("Whole-run deadline exceeded") from error
                raise
        if check and code:
            raise SetupError(
                f"Command failed (exit {code}); see {destination or self.setup_log}"
            )
        return code


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=0.5)


@contextlib.contextmanager
def handle_signals(*, ignore: bool = False) -> Generator[None]:
    """Convert interrupts to reportable errors, or defer them during stack teardown."""
    previous = [
        (signum, signal.getsignal(signum)) for signum in (signal.SIGINT, signal.SIGTERM)
    ]
    for signum, _handler in previous:
        signal.signal(signum, signal.SIG_IGN if ignore else _interrupt)
    try:
        yield
    finally:
        for signum, handler in previous:
            signal.signal(signum, handler)


def _interrupt(signum: int, frame: FrameType | None) -> None:
    raise RunInterruptedError(
        signum, location=frame.f_code.co_name if frame else "execution"
    )
