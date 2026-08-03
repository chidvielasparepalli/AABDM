from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..followups import generate_followups, send_followup
from ..models import Client, FollowUp
from ..schemas import FollowUpOut

router = APIRouter(prefix="/clients/{client_id}/follow-ups", tags=["follow-ups"])


def _get_client(client_id: int, db: Session) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def create_followups(db: Session, client_id: int, call_id: int, outcome: str, service: str | None) -> None:
    """Called by the call engine on completion — creates pending follow-ups."""
    client = _get_client(client_id, db)
    for item in generate_followups(client.name, service, outcome):
        db.add(
            FollowUp(
                client_id=client_id,
                call_id=call_id,
                kind=item["kind"],
                channel=item["channel"],
                content=item["content"],
            )
        )
    db.commit()


@router.get("", response_model=list[FollowUpOut])
def list_followups(client_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    _get_client(client_id, db)
    return (
        db.query(FollowUp)
        .filter(FollowUp.client_id == client_id)
        .order_by(FollowUp.created_at.desc())
        .all()
    )


@router.post("/{followup_id}/send", response_model=FollowUpOut)
async def send(client_id: int, followup_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    client = _get_client(client_id, db)
    followup = db.get(FollowUp, followup_id)
    if not followup or followup.client_id != client_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    to = client.email or client.phone or "unconfigured"
    followup.status = await send_followup(followup.channel, to, followup.content)
    db.commit()
    db.refresh(followup)
    return followup
