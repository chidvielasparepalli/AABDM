from fastapi import APIRouter, Depends

from ..services import BiService
from ..services.deps import service_dep

router = APIRouter(prefix="/clients/{client_id}/bi", tags=["bi"])


@router.get("")
def get_bi(
    client_id: int,
    svc: BiService = Depends(service_dep(BiService)),
):
    return svc.get(client_id)
