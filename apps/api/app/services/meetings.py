"""MeetingService — booking, status, and the outcome-driven auto-book."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from ..domain.enums import CallOutcome
from ..repositories import ClientRepository, MeetingRepository
from .base import Service

BOOKED_MEETING_OUTCOMES = {CallOutcome.MEETING_REQUESTED}


def next_business_morning(now: datetime | None = None) -> datetime:
    """Next weekday 10:00 UTC — deterministic booking slot.

    ponytail: slots are UTC-anchored; operator-timezone-aware scheduling
    arrives with the calendar provider abstraction.
    """
    now = now or datetime.now(timezone.utc)
    candidate = now + timedelta(days=1)
    while candidate.weekday() >= 5:  # sat/sun
        candidate += timedelta(days=1)
    return candidate.replace(hour=10, minute=0, second=0, microsecond=0)


class MeetingService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.meetings = MeetingRepository(db, org_id)

    def book_from_outcome(self, client_id: int, call_id: int, outcome: str):
        """Book a meeting when a call ends positively. Returns None otherwise."""
        if outcome not in BOOKED_MEETING_OUTCOMES:
            return None
        client = self.clients.get(client_id)
        if not client:
            return None
        meeting = self.meetings.create(
            client_id=client_id,
            title=f"Discovery call — {client.name}",
            scheduled_at=next_business_morning(),
        )
        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def list(self, upcoming_only: bool, limit: int, offset: int):
        return self.meetings.list(upcoming_only, limit, offset)

    def create(self, client_id: int, title: str, scheduled_at: datetime):
        if not self.clients.get(client_id):
            raise HTTPException(status_code=404, detail="Client not found")
        meeting = self.meetings.create(client_id=client_id, title=title, scheduled_at=scheduled_at)
        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def set_status(self, meeting_id: int, status: str):
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting.status = status
        self.db.commit()
        self.db.refresh(meeting)
        return meeting
