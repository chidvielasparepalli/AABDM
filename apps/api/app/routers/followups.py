from fastapi import APIRouter, Depends, Query

from ..schemas import FollowUpOut
from ..services import FollowUpService
from ..services.deps import service_dep

router = APIRouter(prefix="/clients/{client_id}/follow-ups", tags=["follow-ups"])


@router.get("", response_model=list[FollowUpOut])
def list_followups(
    client_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: FollowUpService = Depends(service_dep(FollowUpService)),
):
    return svc.list(client_id, limit, offset)


@router.post("/{followup_id}/send", response_model=FollowUpOut)
async def send(
    client_id: int,
    followup_id: int,
    svc: FollowUpService = Depends(service_dep(FollowUpService)),
):
    return await svc.send(client_id, followup_id)
