from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..auth import CurrentUser
from ..db import get_db
from ..models import Client, Email, TimelineEvent
from ..schemas import (
    ClientCreate,
    ClientDetail,
    ClientOut,
    ClientUpdate,
    EmailCreate,
    EmailOut,
    TimelineCreate,
    TimelineOut,
)

router = APIRouter(prefix="/clients", tags=["clients"])


def _get_client(client_id: int, db: Session) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), _: dict = CurrentUser):
    return db.query(Client).order_by(Client.created_at.desc()).all()


@router.post("", response_model=ClientOut, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), _: dict = CurrentUser):
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(client_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    client = (
        db.query(Client)
        .options(
            selectinload(Client.calls),
            selectinload(Client.timeline),
            selectinload(Client.documents),
            selectinload(Client.emails),
        )
        .filter(Client.id == client_id)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int, payload: ClientUpdate, db: Session = Depends(get_db), _: dict = CurrentUser
):
    client = _get_client(client_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    client = _get_client(client_id, db)
    db.delete(client)
    db.commit()


@router.post("/{client_id}/timeline", response_model=TimelineOut, status_code=201)
def add_timeline_event(
    client_id: int, payload: TimelineCreate, db: Session = Depends(get_db), _: dict = CurrentUser
):
    _get_client(client_id, db)
    event = TimelineEvent(client_id=client_id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{client_id}/emails", response_model=EmailOut, status_code=201)
def add_email(
    client_id: int, payload: EmailCreate, db: Session = Depends(get_db), _: dict = CurrentUser
):
    _get_client(client_id, db)
    email = Email(client_id=client_id, **payload.model_dump())
    db.add(email)
    db.commit()
    db.refresh(email)
    return email
