"""BiService — build business intelligence from a completed research report."""

from fastapi import HTTPException

from ..bi import ClientInfo, Research, build_bi
from ..domain.enums import ResearchStatus
from ..repositories import ClientRepository, ResearchReportRepository
from .base import Service


class BiService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.research = ResearchReportRepository(db, org_id)

    def get(self, client_id: int):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        report = self.research.latest(client_id)
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
