from fastapi import APIRouter, BackgroundTasks, Depends

from ..schemas import ResearchReportOut
from ..services import ResearchService
from ..services.deps import service_dep

router = APIRouter(prefix="/clients/{client_id}/research", tags=["research"])


@router.post("", response_model=ResearchReportOut, status_code=201)
def start_research(
    client_id: int,
    background: BackgroundTasks,
    svc: ResearchService = Depends(service_dep(ResearchService)),
):
    return svc.start(client_id, background)


@router.get("", response_model=ResearchReportOut)
def latest_report(
    client_id: int,
    svc: ResearchService = Depends(service_dep(ResearchService)),
):
    return svc.latest(client_id)
