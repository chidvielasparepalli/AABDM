"""Task and Result models for the worker layer."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Callable


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


class TaskPayload(StrEnum):
    """Registry of known task kinds. Adapter maps kind → handler."""

    RESEARCH = "research"
    CALL_REPLAY = "call_replay"
    FOLLOWUP_SEND = "followup_send"
    MEMORY_EXTRACT = "memory_extract"
    LEARNING_REVIEW = "learning_review"


@dataclass
class Task:
    id: str = field(default_factory=_new_id)
    kind: TaskPayload = TaskPayload.RESEARCH
    payload: dict = field(default_factory=dict)
    org_id: int = 1
    attempts: int = 0  # times executed so far
    max_attempts: int = 3
    created_at: datetime = field(default_factory=_now)


@dataclass
class TaskResult:
    """Outcome of one task execution, stored by the worker."""

    task_id: str
    status: TaskStatus
    handler: str
    error: str | None = None
    attempts: int = 0
    started_at: datetime = field(default_factory=_now)
    finished_at: datetime | None = None
    data: dict | None = None


# A handler executes one task kind. Returns result data or raises.
TaskHandler = Callable[[Task], dict]
