from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..domain.enums import CallOutcome
from ..models import Meeting
from ..repositories import ClientRepository, MeetingRepository
from ..schemas import MeetingCreate, MeetingOut, MeetingStatusUpdate
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/meetings", tags=["meetings"])

BOOKED_MEETING_OUTCOMES = {CallOutcome.MEETING_REQUESTED}


def _next_business_morning(now: datetime | None = None) -> datetime:
    """Next weekday 10:00 UTC — deterministic booking slot.

    ponytail: slots are UTC-anchored; operator-timezone-aware scheduling
    arrives with the calendar provider abstraction.
    """
    now = now or datetime.now(timezone.utc)
    candidate = now + timedelta(days=1)
    while candidate.weekday() >= 5:  # sat/sun
        candidate += timedelta(days=1)
    return candidate.replace(hour=10, minute=0, second=0, microsecond=0)


def auto_book_meeting(db: Session, org_id: int, client_id: int, call_id: int, outcome: str) -> Meeting | None:
    """Book a meeting when a call ends positively. Returns None otherwise."""
    if outcome not in BOOKED_MEETING_OUTCOMES:
        return None
    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        return None
    repo = MeetingRepository(db, org_id)
    meeting = repo.create(
        client_id=client_id,
        title=f"Discovery call — {client.name}",
        scheduled_at=_next_business_morning(),
    )
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("", response_model=list[MeetingOut])
def list_meetings(
    upcoming_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    return MeetingRepository(db, org_id).list(upcoming_only, limit, offset)


@router.post("", response_model=MeetingOut, status_code=201)
def create_meeting(
    payload: MeetingCreate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = ClientRepository(db, org_id).get(payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    repo = MeetingRepository(db, org_id)
    meeting = repo.create(
        client_id=payload.client_id,
        title=payload.title,
        scheduled_at=payload.scheduled_at,
    )
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/status", response_model=MeetingOut)
def set_meeting_status(
    meeting_id: int,
    payload: MeetingStatusUpdate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    meeting = MeetingRepository(db, org_id).get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting.status = payload.status
    db.commit()
    db.refresh(meeting)
    return meeting
