from fastapi import APIRouter, Depends

from ..schemas import NegotiationConfigOut, NegotiationConfigUpdate
from ..services import NegotiationService
from ..services.deps import service_dep

router = APIRouter(prefix="/clients/{client_id}/negotiation", tags=["negotiation"])


@router.get("", response_model=NegotiationConfigOut)
def get_config(
    client_id: int,
    svc: NegotiationService = Depends(service_dep(NegotiationService)),
):
    return svc.get(client_id)


@router.put("", response_model=NegotiationConfigOut)
def update_config(
    client_id: int,
    payload: NegotiationConfigUpdate,
    svc: NegotiationService = Depends(service_dep(NegotiationService)),
):
    return svc.update(client_id, payload.model_dump(exclude_unset=True))
