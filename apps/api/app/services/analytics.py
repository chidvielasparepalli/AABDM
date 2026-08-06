"""AnalyticsService — org-scoped aggregates."""

from ..analytics import build_analytics
from ..repositories import CallRepository, ClientRepository, MeetingRepository
from .base import Service


class AnalyticsService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.calls = CallRepository(db, org_id)
        self.meetings = MeetingRepository(db, org_id)

    def get(self) -> dict:
        clients = self.clients.all()
        calls = self.calls.all()
        meetings = self.meetings.all()
        return build_analytics(clients, calls, meetings)
