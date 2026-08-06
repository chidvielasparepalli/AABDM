from fastapi import APIRouter, Depends, Query

from ..schemas import MeetingCreate, MeetingOut, MeetingStatusUpdate
from ..services import MeetingService
from ..services.deps import service_dep

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=list[MeetingOut])
def list_meetings(
    upcoming_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: MeetingService = Depends(service_dep(MeetingService)),
):
    return svc.list(upcoming_only, limit, offset)


@router.post("", response_model=MeetingOut, status_code=201)
def create_meeting(
    payload: MeetingCreate,
    svc: MeetingService = Depends(service_dep(MeetingService)),
):
    return svc.create(payload.client_id, payload.title, payload.scheduled_at)


@router.post("/{meeting_id}/status", response_model=MeetingOut)
def set_meeting_status(
    meeting_id: int,
    payload: MeetingStatusUpdate,
    svc: MeetingService = Depends(service_dep(MeetingService)),
):
    return svc.set_status(meeting_id, payload.status)
