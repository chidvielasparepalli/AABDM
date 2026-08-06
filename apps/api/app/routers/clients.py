from fastapi import APIRouter, Depends, Query

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
from ..services import ClientService
from ..services.deps import service_dep

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: ClientService = Depends(service_dep(ClientService)),
):
    return svc.list(limit, offset)


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientCreate,
    svc: ClientService = Depends(service_dep(ClientService)),
):
    return svc.create(payload.model_dump())


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(
    client_id: int,
    svc: ClientService = Depends(service_dep(ClientService)),
):
    return svc.get(client_id)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    svc: ClientService = Depends(service_dep(ClientService)),
):
    return svc.update(client_id, payload.model_dump(exclude_unset=True))


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    svc: ClientService = Depends(service_dep(ClientService)),
):
    svc.delete(client_id)


@router.post("/{client_id}/timeline", response_model=TimelineOut, status_code=201)
def add_timeline_event(
    client_id: int,
    payload: TimelineCreate,
    svc: ClientService = Depends(service_dep(ClientService)),
):
    return svc.add_timeline(client_id, payload.event)


@router.post("/{client_id}/emails", response_model=EmailOut, status_code=201)
def add_email(
    client_id: int,
    payload: EmailCreate,
    svc: ClientService = Depends(service_dep(ClientService)),
):
    return svc.add_email(client_id, payload.model_dump())
