from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Client, NegotiationConfig
from ..schemas import NegotiationConfigOut, NegotiationConfigUpdate

router = APIRouter(prefix="/clients/{client_id}/negotiation", tags=["negotiation"])


@router.get("", response_model=NegotiationConfigOut)
def get_config(client_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    config = db.query(NegotiationConfig).filter(NegotiationConfig.client_id == client_id).first()
    if not config:
        config = NegotiationConfig(
            client_id=client_id,
            pricing=[],
            discounts=[],
            freebies=[],
            payment_terms=[],
            escalation_rules=[],
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.put("", response_model=NegotiationConfigOut)
def update_config(
    client_id: int,
    payload: NegotiationConfigUpdate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    config = db.query(NegotiationConfig).filter(NegotiationConfig.client_id == client_id).first()
    if not config:
        config = NegotiationConfig(client_id=client_id)
        db.add(config)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config
