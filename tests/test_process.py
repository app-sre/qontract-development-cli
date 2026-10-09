from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from typing import TYPE_CHECKING
from unittest.mock import Mock, call

import pytest

from qontract_development_cli import process
from qontract_development_cli.process import Runner, RunTimeoutError, SetupError

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("size", [10, 131072])
@pytest.mark.parametrize("exit_code", [0, 7])
def test_real_subprocess_output_is_complete_and_exit_status_is_preserved(
    tmp_path: Path,
    size: int,
    exit_code: int,
) -> None:
    setup = tmp_path / "setup.log"
    output = tmp_path / "integration.log"
    runner = Runner(deadline=time.monotonic() + 10, setup_log=setup)
    result = runner.run(
        [
            sys.executable,
            "-c",
            f"import os,sys; os.write(1,b'a'*{size}); os.write(2,b'error\\n'); sys.exit({exit_code})",
        ],
        destination=output,
        check=False,
    )
    assert result == exit_code
    assert output.read_bytes() == b"a" * size + b"error\n"
    assert not setup.exists()


def test_checked_subprocess_failure_retains_stderr(tmp_path: Path) -> None:
    log = tmp_path / "setup.log"
    runner = Runner(deadline=time.monotonic() + 10, setup_log=log)
    with pytest.raises(SetupError, match=r"exit 7"):
        runner.run([
            sys.executable,
            "-c",
            "import sys; sys.stderr.write('failed\\n'); sys.exit(7)",
        ])
    assert log.read_text() == "failed\n"


def test_real_subprocess_timeout_retains_output_and_returns_promptly(
    tmp_path: Path,
) -> None:
    started = time.monotonic()
    timeout_budget = 5
    log = tmp_path / "setup.log"
    runner = Runner(deadline=started + 0.5, setup_log=log)
    with pytest.raises(RunTimeoutError, match="deadline exceeded"):
        runner.run([
            sys.executable,
            "-c",
            "import time; print('started',flush=True); time.sleep(30)",
        ])
    assert time.monotonic() - started < timeout_budget
    assert log.read_text() == "started\n"


def test_expired_deadline_does_not_spawn_a_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spawn = Mock()
    monkeypatch.setattr(subprocess, "Popen", spawn)
    runner = Runner(deadline=time.monotonic() - 1, setup_log=tmp_path / "setup.log")
    with pytest.raises(RunTimeoutError, match="deadline exceeded"):
        runner.run([sys.executable, "-c", "raise AssertionError('must not run')"])
    spawn.assert_not_called()


def test_subprocess_termination_escalates_only_its_process_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    child = Mock(spec=subprocess.Popen)
    child.pid = 12345
    child.poll.return_value = None
    child.wait.side_effect = [
        subprocess.TimeoutExpired("test", 10),
        subprocess.TimeoutExpired("test", 0.5),
        0,
    ]
    kill = Mock()
    monkeypatch.setattr(os, "killpg", kill)
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=child))
    monkeypatch.setattr(time, "monotonic", lambda: 10)
    runner = Runner(deadline=20, setup_log=tmp_path / "setup.log")
    with pytest.raises(RunTimeoutError, match="deadline exceeded"):
        runner.run([sys.executable, "-c", "pass"])
    assert kill.call_args_list == [
        call(12345, signal.SIGTERM),
        call(12345, signal.SIGKILL),
    ]
    assert child.wait.call_args_list == [
        call(timeout=10),
        call(timeout=0.5),
        call(timeout=0.5),
    ]


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_signal_is_reportable_and_previous_handler_is_restored(
    signum: signal.Signals,
) -> None:
    previous = signal.getsignal(signum)
    with (
        pytest.raises(process.RunInterruptedError, match=f"Received {signum.name}"),
        process.handle_signals(),
    ):
        signal.raise_signal(signum)
    assert signal.getsignal(signum) == previous


def test_cleanup_temporarily_ignores_interrupts() -> None:
    previous = [signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)]
    with process.handle_signals(ignore=True):
        assert signal.getsignal(signal.SIGINT) == signal.SIG_IGN
        assert signal.getsignal(signal.SIGTERM) == signal.SIG_IGN
    assert [
        signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    ] == previous
