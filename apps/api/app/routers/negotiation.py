from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..repositories import ClientRepository, NegotiationConfigRepository
from ..schemas import NegotiationConfigOut, NegotiationConfigUpdate
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/clients/{client_id}/negotiation", tags=["negotiation"])


@router.get("", response_model=NegotiationConfigOut)
def get_config(
    client_id: int,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    repo = NegotiationConfigRepository(db, org_id)
    config = repo.for_client(client_id)
    if not config:
        config = repo.add(
            client_id=client_id,
            pricing=[],
            discounts=[],
            freebies=[],
            payment_terms=[],
            escalation_rules=[],
        )
        db.commit()
        db.refresh(config)
    return config


@router.put("", response_model=NegotiationConfigOut)
def update_config(
    client_id: int,
    payload: NegotiationConfigUpdate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    repo = NegotiationConfigRepository(db, org_id)
    config = repo.for_client(client_id)
    if not config:
        config = repo.add(client_id=client_id)
        db.add(config)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config
