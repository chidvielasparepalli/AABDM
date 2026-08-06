"""Event sink for worker outcomes: protocol + in-memory implementation (mock).

The protocol is the contract the real Event Bus (M3) implements. MemoryBus
records events in-memory for the mock pipeline and tests.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from .models import TaskResult


@dataclass(frozen=True)
class WorkerEvent:
    type: str  # worker.task_success | worker.task_failed | ...
    task_id: str
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus(Protocol):
    def publish(self, event: WorkerEvent) -> None:
        """Record/publish an event. Subscribers react, producers never block."""
        ...


class MemoryBus:
    """In-memory event sink. Mock — no persistence, no fan-out."""

    def __init__(self) -> None:
        self.events: list[WorkerEvent] = []

    def publish(self, event: WorkerEvent) -> None:
        self.events.append(event)

    def by_type(self, event_type: str) -> list[WorkerEvent]:
        return [e for e in self.events if e.type == event_type]


def task_result_event(result: TaskResult) -> WorkerEvent:
    """Map a completed TaskResult to a bus event."""
    if result.status.value == "success":
        return WorkerEvent(
            type="worker.task_success",
            task_id=result.task_id,
            payload={"handler": result.handler, "attempts": result.attempts, "data": result.data or {}},
        )
    return WorkerEvent(
        type="worker.task_failed",
        task_id=result.task_id,
        payload={
            "handler": result.handler,
            "attempts": result.attempts,
            "error": result.error,
            "dead_lettered": result.status.value == "dead_lettered",
        },
    )
