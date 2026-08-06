from fastapi import APIRouter, Depends, Query

from ..schemas import MemoryOut
from ..services import MemoryService
from ..services.deps import service_dep

router = APIRouter(prefix="/clients/{client_id}/memory", tags=["memory"])


@router.get("", response_model=list[MemoryOut])
def list_memories(
    client_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: MemoryService = Depends(service_dep(MemoryService)),
):
    return svc.list(client_id, limit, offset)
