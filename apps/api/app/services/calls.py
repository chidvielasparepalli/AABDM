"""CallService — call lifecycle + the post-call saga.

The saga (replay → book meeting → follow-ups → memories → learning review)
previously lived in the calls router; it now runs here as the orchestration
boundary where workflows/agents will plug in later.
"""

import asyncio

from fastapi import BackgroundTasks, HTTPException

from ..bi import ClientInfo, Research, build_bi
from ..calls import STAGES, replay_call
from ..db import SessionLocal
from ..domain.enums import CallStatus
from ..repositories import (
    CallRepository,
    ClientRepository,
    NegotiationConfigRepository,
    ResearchReportRepository,
)
from .base import Service
from .followups import FollowUpService
from .learning import LearningService
from .meetings import MeetingService
from .memory import MemoryService


class CallService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.calls = CallRepository(db, org_id)

    def start(self, client_id: int, background: BackgroundTasks):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        if self.calls.find_running(client_id):
            raise HTTPException(status_code=409, detail="A call is already in progress")

        call = self.calls.create(client_id=client_id, status=CallStatus.RUNNING, stage=STAGES[0])
        self.db.commit()
        self.db.refresh(call)

        bi = self._bi_for(client_id)
        negotiation = self._negotiation_for(client_id)
        background.add_task(
            self.replay_and_save,
            call.id,
            client_id,
            client.name,
            bi,
            negotiation,
            self.org_id,
        )
        return call

    def list(self, client_id: int, limit: int, offset: int):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return self.calls.list_for_client(client_id, limit, offset)

    def get(self, client_id: int, call_id: int):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        call = self.calls.get(call_id)
        if not call or call.client_id != client_id:
            raise HTTPException(status_code=404, detail="Call not found")
        return call

    def _bi_for(self, client_id: int) -> dict:
        """Latest completed research → BI report, or default when none."""
        report = ResearchReportRepository(self.db, self.org_id).latest_done(client_id)
        if not report:
            return {
                "opportunity_score": 50,
                "budget_estimate": {"min": 1000, "max": 4000},
                "recommended_service": None,
            }
        client = self.clients.get(client_id)
        research = Research(
            seo_score=report.seo_score,
            performance_score=report.performance_score,
            tech_stack=report.tech_stack or [],
            missing_features=report.missing_features or [],
            opportunities=report.opportunities or [],
            competitors=report.competitors or [],
        )
        return build_bi(ClientInfo(client.name, client.industry, client.budget), research)

    def _negotiation_for(self, client_id: int) -> dict:
        config = NegotiationConfigRepository(self.db, self.org_id).for_client(client_id)
        if not config:
            return {}
        return {
            "pricing": config.pricing or [],
            "discounts": config.discounts or [],
            "freebies": config.freebies or [],
            "payment_terms": config.payment_terms or [],
            "escalation_rules": config.escalation_rules or [],
        }

    @staticmethod
    def replay_and_save(
        call_id: int, client_id: int, client_name: str, bi: dict, negotiation: dict, org_id: int
    ) -> None:
        """Background saga: replay the call, then the outcome chain. Own session (thread)."""
        db = SessionLocal()
        try:
            calls = CallRepository(db, org_id)
            call = calls.get(call_id)
            if not call:
                return
            call.status = CallStatus.RUNNING
            db.commit()

            async def write(line) -> None:
                # fresh session per write: background thread owns it
                nonlocal call
                if call not in db:
                    call = calls.get(call_id)
                calls.add_transcript(
                    call_id,
                    role=line.role,
                    text=line.text,
                    stage=line.stage,
                    emotion=line.emotion,
                    confidence=line.confidence,
                )
                call.stage = line.stage
                db.commit()

            outcome, duration_s, sentiment = asyncio.run(replay_call(client_name, bi, write, negotiation))
            call.status = CallStatus.DONE
            call.outcome = outcome
            call.duration_s = duration_s
            call.sentiment = sentiment
            db.commit()
            MeetingService(db, org_id).book_from_outcome(client_id, call.id, outcome)
            FollowUpService(db, org_id).create_from_outcome(
                client_id, call.id, outcome, bi.get("recommended_service")
            )
            MemoryService(db, org_id).extract_from_call(call.id)
            LearningService(db, org_id).review_and_store(call.id)
        finally:
            db.close()
