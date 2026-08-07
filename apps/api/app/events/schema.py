"""Event schema — every event, everywhere.

Structure mirrors the design doc: correlation_id threads a business transaction,
causation_id chains events, aggregate_id is the ordering key. All producers
must emit complete metadata so downstream consumers can route, filter, and
replay correctly.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass(frozen=True)
class Event:
    """One fact that happened. Immutable once emitted."""

    type: str
    aggregate: str
    aggregate_id: int | str
    payload: dict = field(default_factory=dict)
    # Tracing
    event_id: str = field(default_factory=_new_id)
    occurred_at: datetime = field(default_factory=_now)
    correlation_id: str = field(default_factory=_new_id)
    causation_id: str | None = None
    # Tenancy
    org_id: int = 1
    # Versioning
    version: int = 1


# Canonical topic derivation: type "research.completed" → topic "research"
def topic_for(event_type: str) -> str:
    return event_type.split(".")[0]


# Event type catalog — single source of truth for every event name.
# Producers import from here; subscribers match on these constants.
class EventType:
    # Research
    RESEARCH_STARTED = "research.started"
    RESEARCH_COMPLETED = "research.completed"
    RESEARCH_FAILED = "research.failed"

    # Business Intelligence
    BI_COMPLETED = "bi.completed"

    # Calls
    CALL_STARTED = "call.started"
    CALL_LINE = "call.line"
    CALL_COMPLETED = "call.completed"
    CALL_FAILED = "call.failed"

    # Meetings
    MEETING_BOOKED = "meeting.booked"
    MEETING_CONFIRMED = "meeting.confirmed"
    MEETING_CANCELLED = "meeting.cancelled"

    # Follow-ups
    FOLLOWUP_DRAFTED = "followup.drafted"
    FOLLOWUP_SENT = "followup.sent"
    FOLLOWUP_FAILED = "followup.failed"

    # Memory
    MEMORY_EXTRACTED = "memory.extracted"

    # Learning
    LEARNING_REVIEWED = "learning.reviewed"

    # System
    WORKER_TASK_SUCCESS = "worker.task_success"
    WORKER_TASK_FAILED = "worker.task_failed"


def make_event(
    event_type: str,
    aggregate: str,
    aggregate_id: int | str,
    payload: dict,
    org_id: int = 1,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> Event:
    """Factory: emit a correctly-shaped event with tracing populated."""
    return Event(
        type=event_type,
        aggregate=aggregate,
        aggregate_id=aggregate_id,
        payload=payload,
        org_id=org_id,
        correlation_id=correlation_id or uuid.uuid4().hex,
        causation_id=causation_id,
    )