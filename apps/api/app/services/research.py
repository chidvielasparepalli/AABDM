"""ResearchService — start/query research, background execution + event publishing."""

import asyncio

from fastapi import BackgroundTasks, HTTPException

from ..db import SessionLocal
from ..domain.enums import ResearchStatus
from ..events.bus import bus
from ..events.schema import EventType, make_event
from ..repositories import ClientRepository, ResearchReportRepository
from ..research import run_research
from ..security.errors import SSrfBlocked
from ..security.ssrf import validate_url
from .base import Service


class ResearchService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.research = ResearchReportRepository(db, org_id)

    def start(self, client_id: int, background: BackgroundTasks):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        url = client.website
        if not url:
            raise HTTPException(status_code=400, detail="Client has no website set")

        # Fail fast before spawning a background job: blocked URLs → 400,
        # not a 500 half-way through research.
        try:
            validate_url(url)
        except SSrfBlocked as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        report = self.research.create(client_id=client_id, url=url)
        self.db.commit()
        self.db.refresh(report)

        # Emit research.started event
        event = make_event(
            event_type=EventType.RESEARCH_STARTED,
            aggregate="research",
            aggregate_id=report.id,
            payload={"client_id": client_id, "url": url},
            org_id=self.org_id,
        )
        background.add_task(self._emit, event)

        background.add_task(self.run_and_save, report.id, url, self.org_id)
        return report

    @staticmethod
    def _emit(event) -> None:
        """Emit an event on the bus (async)."""
        asyncio.run(bus.publish(event))

    def latest(self, client_id: int):
        if not self.clients.get(client_id):
            raise HTTPException(status_code=404, detail="Client not found")
        report = self.research.latest(client_id)
        if not report:
            raise HTTPException(status_code=404, detail="No research report yet")
        return report

    @staticmethod
    def run_and_save(report_id: int, url: str, org_id: int) -> None:
        """Background: run research, persist result, emit completed/failed event."""
        from ..db import SessionLocal
        from ..events.bus import bus
        from ..events.schema import EventType, make_event
        from ..repositories import ResearchReportRepository

        db = SessionLocal()
        try:
            repo = ResearchReportRepository(db, org_id)
            report = repo.get(report_id)
            if not report:
                return
            try:
                result = asyncio.run(run_research(url))
                for k, v in result.items():
                    setattr(report, k, v)
                event_type = EventType.RESEARCH_COMPLETED
            except Exception as exc:  # noqa: BLE001 — persist any failure
                report.status = ResearchStatus.ERROR
                report.error = str(exc)
                event_type = EventType.RESEARCH_FAILED
            db.commit()

            # Emit completion/failed event
            event = make_event(
                event_type=event_type,
                aggregate="research",
                aggregate_id=report.id,
                payload={"client_id": report.client_id, "url": url},
                org_id=org_id,
            )
            asyncio.run(bus.publish(event))
        finally:
            db.close()