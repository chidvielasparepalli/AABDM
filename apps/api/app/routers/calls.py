import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..bi import ClientInfo, Research, build_bi
from ..calls import STAGES, replay_call
from ..db import SessionLocal, get_db
from ..domain.enums import CallStatus
from ..models import Client
from ..repositories import (
    CallRepository,
    ClientRepository,
    NegotiationConfigRepository,
    ResearchReportRepository,
)
from ..schemas import CallDetail, CallOut
from ..tenancy import CurrentOrg
from .calendar import auto_book_meeting
from .followups import create_followups
from .learning import review_and_store
from .memory import extract_from_call

router = APIRouter(prefix="/clients/{client_id}/calls", tags=["calls"])


def _get_client(db: Session, org_id: int, client_id: int) -> Client:
    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def _bi_for(db: Session, org_id: int, client_id: int) -> dict:
    """Latest completed research → BI report, or default when none."""
    report = ResearchReportRepository(db, org_id).latest_done(client_id)
    if not report:
        return {
            "opportunity_score": 50,
            "budget_estimate": {"min": 1000, "max": 4000},
            "recommended_service": None,
        }
    client = ClientRepository(db, org_id).get(client_id)
    research = Research(
        seo_score=report.seo_score,
        performance_score=report.performance_score,
        tech_stack=report.tech_stack or [],
        missing_features=report.missing_features or [],
        opportunities=report.opportunities or [],
        competitors=report.competitors or [],
    )
    return build_bi(ClientInfo(client.name, client.industry, client.budget), research)


def _negotiation_for(db: Session, org_id: int, client_id: int) -> dict:
    config = NegotiationConfigRepository(db, org_id).for_client(client_id)
    if not config:
        return {}
    return {
        "pricing": config.pricing or [],
        "discounts": config.discounts or [],
        "freebies": config.freebies or [],
        "payment_terms": config.payment_terms or [],
        "escalation_rules": config.escalation_rules or [],
    }


def _replay_and_save(call_id: int, client_id: int, client_name: str, bi: dict, negotiation: dict, org_id: int) -> None:
    db = SessionLocal()
    try:
        repo = CallRepository(db, org_id)
        call = repo.get(call_id)
        if not call:
            return
        call.status = CallStatus.RUNNING
        db.commit()

        async def write(line) -> None:
            # fresh session per write: background thread owns it
            nonlocal call
            if call not in db:
                call = repo.get(call_id)
            repo.add_transcript(
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
        auto_book_meeting(db, org_id, client_id, call.id, outcome)
        create_followups(db, org_id, client_id, call.id, outcome, bi.get("recommended_service"))
        extract_from_call(db, org_id, call.id)
        review_and_store(db, org_id, call.id)
    finally:
        db.close()


@router.post("", response_model=CallOut, status_code=201)
def start_call(
    client_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = _get_client(db, org_id, client_id)

    running = CallRepository(db, org_id).find_running(client_id)
    if running:
        raise HTTPException(status_code=409, detail="A call is already in progress")

    repo = CallRepository(db, org_id)
    call = repo.create(client_id=client_id, status=CallStatus.RUNNING, stage=STAGES[0])
    db.commit()
    db.refresh(call)

    bi = _bi_for(db, org_id, client_id)
    negotiation = _negotiation_for(db, org_id, client_id)
    background.add_task(_replay_and_save, call.id, client_id, client.name, bi, negotiation, org_id)
    return call


@router.get("", response_model=list[CallOut])
def list_calls(
    client_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    _get_client(db, org_id, client_id)
    return CallRepository(db, org_id).list_for_client(client_id, limit, offset)


@router.get("/{call_id}", response_model=CallDetail)
def get_call(
    client_id: int,
    call_id: int,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    _get_client(db, org_id, client_id)
    call = CallRepository(db, org_id).get(call_id)
    if not call or call.client_id != client_id:
        raise HTTPException(status_code=404, detail="Call not found")
    return call
