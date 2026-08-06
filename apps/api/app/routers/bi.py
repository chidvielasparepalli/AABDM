from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..bi import ClientInfo, Research, build_bi
from ..db import get_db
from ..domain.enums import ResearchStatus
from ..repositories import ClientRepository, ResearchReportRepository
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/clients/{client_id}/bi", tags=["bi"])


@router.get("")
def get_bi(
    client_id: int,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    report = ResearchReportRepository(db, org_id).latest(client_id)
    if not report or report.status != ResearchStatus.DONE:
        raise HTTPException(status_code=409, detail="No completed research yet")

    research = Research(
        seo_score=report.seo_score,
        performance_score=report.performance_score,
        tech_stack=report.tech_stack or [],
        missing_features=report.missing_features or [],
        opportunities=report.opportunities or [],
        competitors=report.competitors or [],
    )
    info = ClientInfo(
        name=client.name,
        industry=client.industry,
        budget=client.budget,
    )
    return build_bi(info, research)
