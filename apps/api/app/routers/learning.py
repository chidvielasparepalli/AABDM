from fastapi import APIRouter, Depends, Query

from ..schemas import LearningEntryOut, LearningStats
from ..services import LearningService
from ..services.deps import service_dep

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("", response_model=list[LearningEntryOut])
def list_entries(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: LearningService = Depends(service_dep(LearningService)),
):
    return svc.list(limit, offset)


@router.get("/stats", response_model=LearningStats)
def stats(
    svc: LearningService = Depends(service_dep(LearningService)),
):
    return svc.stats()
