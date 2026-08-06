from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..analytics import build_analytics
from ..auth import CurrentUser
from ..db import get_db
from ..models import Call, Client, Meeting

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def get_analytics(db: Session = Depends(get_db), _: dict = CurrentUser):
    clients = db.query(Client).all()
    calls = db.query(Call).all()
    meetings = db.query(Meeting).all()
    return build_analytics(clients, calls, meetings)
