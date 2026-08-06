from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..analytics import build_analytics
from ..auth import CurrentUser
from ..db import get_db
from ..repositories import CallRepository, ClientRepository, MeetingRepository
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def get_analytics(
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    clients = ClientRepository(db, org_id).all()
    calls = CallRepository(db, org_id).all()
    meetings = MeetingRepository(db, org_id).all()
    return build_analytics(clients, calls, meetings)
