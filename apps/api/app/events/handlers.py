"""Event handlers — real async service calls.

Each handler creates a scoped session + org_id from the event, instantiates
the appropriate service, and calls the saga method. Errors are isolated;
the bus never retries — idempotency is the handler's responsibility.
"""

from app.events.bus import bus
from app.events.schema import EventType
from app.db import SessionLocal
from app.services import (
    BiService,
    FollowUpService,
    MeetingService,
    MemoryService,
    LearningService,
)


async def handle_research_completed(event) -> None:
    """research.completed → BiService.get (triggers BI engine)."""
    org_id = event.org_id
    client_id = event.payload.get("client_id")
    if client_id is None:
        return
    db = SessionLocal()
    try:
        BiService(db, org_id).get(client_id)
    finally:
        db.close()


async def handle_call_meeting(event) -> None:
    """call.completed → MeetingService.book_from_outcome."""
    org_id = event.org_id
    client_id = event.payload.get("client_id")
    call_id = event.payload.get("call_id")
    outcome = event.payload.get("outcome")
    if not (client_id and call_id and outcome):
        return
    db = SessionLocal()
    try:
        from app.services import MeetingService
        MeetingService(db, org_id).book_from_outcome(client_id, call_id, outcome)
    finally:
        db.close()


async def handle_call_followups(event) -> None:
    """call.completed → FollowUpService.create_from_outcome."""
    org_id = event.org_id
    client_id = event.payload.get("client_id")
    call_id = event.payload.get("call_id")
    outcome = event.payload.get("outcome")
    service = event.payload.get("recommended_service")
    if not (client_id and call_id and outcome):
        return
    db = SessionLocal()
    try:
        from app.services import FollowUpService
        FollowUpService(db, org_id).create_from_outcome(client_id, call_id, outcome, service)
    finally:
        db.close()


async def handle_call_memory(event) -> None:
    """call.completed → MemoryService.extract_from_call."""
    org_id = event.org_id
    call_id = event.payload.get("call_id")
    if not call_id:
        return
    db = SessionLocal()
    try:
        from app.services import MemoryService
        MemoryService(db, org_id).extract_from_call(call_id)
    finally:
        db.close()


async def handle_call_learning(event) -> None:
    """call.completed → LearningService.review_and_store."""
    org_id = event.org_id
    call_id = event.payload.get("call_id")
    if not call_id:
        return
    db = SessionLocal()
    try:
        from app.services import LearningService
        LearningService(db, org_id).review_and_store(call_id)
    finally:
        db.close()


def register_handlers() -> None:
    """Wire all event subscriptions. Called once at startup."""
    from app.events.bus import bus
    from app.events.schema import EventType

    # Research → BI
    bus.subscribe(EventType.RESEARCH_COMPLETED, handle_research_completed)
    # Call saga — 4 independent subscribers
    bus.subscribe(EventType.CALL_COMPLETED, handle_call_meeting)
    bus.subscribe(EventType.CALL_COMPLETED, handle_call_followups)
    bus.subscribe(EventType.CALL_COMPLETED, handle_call_memory)
    bus.subscribe(EventType.CALL_COMPLETED, handle_call_learning)