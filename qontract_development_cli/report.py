from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Outcome(StrEnum):
    SUCCESS = "success"
    INTEGRATION_FAILURE = "integration_failure"
    SETUP_FAILURE = "setup_failure"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"
    CLEANUP_FAILURE = "cleanup_failure"


class Execution(BaseModel, frozen=True):
    outcome: Outcome
    exit_code: int
    integration_exit_code: int | None = None
    signal: int | None = None
    cleanup_completed: bool = False
    errors: list[str] = Field(default_factory=list)


class RunReport(BaseModel, frozen=True):
    schema_version: Literal[2] = 2
    environment: str
    profile: str
    started_at: datetime
    ended_at: datetime
    timeout_seconds: float
    execution: Execution
    setup_log: Path
    integration_log: Path
    stack_log: Path

    def write(self, path: Path) -> None:
        """Persist the execution result alongside the complete logs."""
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")
