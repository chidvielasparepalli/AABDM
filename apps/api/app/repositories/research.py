"""ResearchReport repo."""

from ..models import ResearchReport
from .base import ModelRepository


class ResearchReportRepository(ModelRepository[ResearchReport]):
    model = ResearchReport

    def create(self, client_id: int, url: str) -> ResearchReport:
        return self.add(client_id=client_id, url=url)

    def latest(self, client_id: int) -> ResearchReport | None:
        return (
            self._base()
            .filter(ResearchReport.client_id == client_id)
            .order_by(ResearchReport.created_at.desc())
            .first()
        )

    def latest_done(self, client_id: int) -> ResearchReport | None:
        from ..domain.enums import ResearchStatus

        return (
            self._base()
            .filter(
                ResearchReport.client_id == client_id,
                ResearchReport.status == ResearchStatus.DONE,
            )
            .order_by(ResearchReport.created_at.desc())
            .first()
        )
