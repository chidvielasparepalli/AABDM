from fastapi import APIRouter, BackgroundTasks, Depends, Query

from ..schemas import CallDetail, CallOut
from ..services import CallService
from ..services.deps import service_dep

router = APIRouter(prefix="/clients/{client_id}/calls", tags=["calls"])


@router.post("", response_model=CallOut, status_code=201)
def start_call(
    client_id: int,
    background: BackgroundTasks,
    svc: CallService = Depends(service_dep(CallService)),
):
    return svc.start(client_id, background)


@router.get("", response_model=list[CallOut])
def list_calls(
    client_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: CallService = Depends(service_dep(CallService)),
):
    return svc.list(client_id, limit, offset)


@router.get("/{call_id}", response_model=CallDetail)
def get_call(
    client_id: int,
    call_id: int,
    svc: CallService = Depends(service_dep(CallService)),
):
    return svc.get(client_id, call_id)
