from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..followups import generate_followups, send_followup
from ..models import Client
from ..repositories import ClientRepository, FollowUpRepository
from ..schemas import FollowUpOut
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/clients/{client_id}/follow-ups", tags=["follow-ups"])


def _get_client(db: Session, org_id: int, client_id: int) -> Client:
    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def create_followups(db: Session, org_id: int, client_id: int, call_id: int, outcome: str, service: str | None) -> None:
    """Called by the call engine on completion — creates pending follow-ups."""
    client = _get_client(db, org_id, client_id)
    repo = FollowUpRepository(db, org_id)
    for item in generate_followups(client.name, service, outcome):
        repo.create(
            client_id=client_id,
            call_id=call_id,
            kind=item["kind"],
            channel=item["channel"],
            content=item["content"],
        )
    db.commit()


@router.get("", response_model=list[FollowUpOut])
def list_followups(
    client_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    _get_client(db, org_id, client_id)
    return FollowUpRepository(db, org_id).list_for_client(client_id, limit, offset)


@router.post("/{followup_id}/send", response_model=FollowUpOut)
async def send(
    client_id: int,
    followup_id: int,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = _get_client(db, org_id, client_id)
    followup = FollowUpRepository(db, org_id).get(followup_id)
    if not followup or followup.client_id != client_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    to = client.email or client.phone or "unconfigured"
    followup.status = await send_followup(followup.channel, to, followup.content)
    db.commit()
    db.refresh(followup)
    return followup
