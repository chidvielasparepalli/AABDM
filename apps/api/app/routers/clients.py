from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..domain.enums import ClientStatus
from ..models import Client
from ..repositories import ClientRepository, EmailRepository, TimelineRepository
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
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/clients", tags=["clients"])


def _client_repo(db: Session, org_id: int) -> ClientRepository:
    return ClientRepository(db, org_id)


def _get_client(db: Session, org_id: int, client_id: int) -> Client:
    client = _client_repo(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("", response_model=list[ClientOut])
def list_clients(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    return _client_repo(db, org_id).list(limit, offset)


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    data = payload.model_dump()
    if data.get("status") is None:
        data["status"] = ClientStatus.LEAD
    client = _client_repo(db, org_id).add(**data)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = _get_client(db, org_id, client_id)
    return client


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = _get_client(db, org_id, client_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = _get_client(db, org_id, client_id)
    db.delete(client)
    db.commit()


@router.post("/{client_id}/timeline", response_model=TimelineOut, status_code=201)
def add_timeline_event(
    client_id: int,
    payload: TimelineCreate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    _get_client(db, org_id, client_id)
    repo = TimelineRepository(db, org_id)
    event = repo.add_for_client(client_id, payload.event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{client_id}/emails", response_model=EmailOut, status_code=201)
def add_email(
    client_id: int,
    payload: EmailCreate,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    _get_client(db, org_id, client_id)
    repo = EmailRepository(db, org_id)
    email = repo.add_for_client(client_id, **payload.model_dump())
    db.commit()
    db.refresh(email)
    return email
