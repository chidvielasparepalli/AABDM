from fastapi import APIRouter, Depends

from ..services import AnalyticsService
from ..services.deps import service_dep

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def get_analytics(
    svc: AnalyticsService = Depends(service_dep(AnalyticsService)),
):
    return svc.get()
