from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Client, Meeting
from ..schemas import MeetingCreate, MeetingOut

router = APIRouter(prefix="/meetings", tags=["meetings"])

BOOKED_MEETING_OUTCOMES = {"Meeting / proposal requested"}


def _next_business_morning(now: datetime | None = None) -> datetime:
    """Next weekday 10:00 local — deterministic booking slot."""
    now = now or datetime.now(timezone.utc)
    candidate = now + timedelta(days=1)
    while candidate.weekday() >= 5:  # sat/sun
        candidate += timedelta(days=1)
    return candidate.replace(hour=10, minute=0, second=0, microsecond=0)


def auto_book_meeting(db: Session, client_id: int, call_id: int, outcome: str) -> Meeting | None:
    """Book a meeting when a call ends positively. Returns None otherwise."""
    if outcome not in BOOKED_MEETING_OUTCOMES:
        return None
    client = db.get(Client, client_id)
    meeting = Meeting(
        client_id=client_id,
        call_id=call_id,
        title=f"Discovery call — {client.name}",
        scheduled_at=_next_business_morning(),
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("", response_model=list[MeetingOut])
def list_meetings(
    upcoming_only: bool = False,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
):
    query = db.query(Meeting)
    if upcoming_only:
        now = datetime.now(timezone.utc)
        query = query.filter(Meeting.scheduled_at >= now, Meeting.status != "cancelled")
    return query.order_by(Meeting.scheduled_at.asc()).all()


@router.post("", response_model=MeetingOut, status_code=201)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db), _: dict = CurrentUser):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    meeting = Meeting(client_id=payload.client_id, title=payload.title, scheduled_at=payload.scheduled_at)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/status", response_model=MeetingOut)
def set_meeting_status(
    meeting_id: int, status: str, db: Session = Depends(get_db), _: dict = CurrentUser
):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting.status = status
    db.commit()
    db.refresh(meeting)
    return meeting
