import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..bi import ClientInfo, Research, build_bi
from ..calls import STAGES, replay_call
from .calendar import auto_book_meeting
from .followups import create_followups
from .memory import extract_from_call
from .learning import review_and_store
from ..db import get_db
from ..models import Call, Client, NegotiationConfig, ResearchReport, TranscriptLine
from ..schemas import CallDetail, CallOut

router = APIRouter(prefix="/clients/{client_id}/calls", tags=["calls"])


def _get_client(client_id: int, db: Session) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def _bi_for(db: Session, client_id: int) -> dict:
    """Latest completed research → BI report, or default when none."""
    report = (
        db.query(ResearchReport)
        .filter(ResearchReport.client_id == client_id, ResearchReport.status == "done")
        .order_by(ResearchReport.created_at.desc())
        .first()
    )
    if not report:
        return {
            "opportunity_score": 50,
            "budget_estimate": {"min": 1000, "max": 4000},
            "recommended_service": None,
        }
    client = db.get(Client, client_id)
    research = Research(
        seo_score=report.seo_score,
        performance_score=report.performance_score,
        tech_stack=report.tech_stack or [],
        missing_features=report.missing_features or [],
        opportunities=report.opportunities or [],
        competitors=report.competitors or [],
    )
    return build_bi(ClientInfo(client.name, client.industry, client.budget), research)


def _negotiation_for(db: Session, client_id: int) -> dict:
    config = db.query(NegotiationConfig).filter(NegotiationConfig.client_id == client_id).first()
    if not config:
        return {}
    return {
        "pricing": config.pricing or [],
        "discounts": config.discounts or [],
        "freebies": config.freebies or [],
        "payment_terms": config.payment_terms or [],
        "escalation_rules": config.escalation_rules or [],
    }


def _replay_and_save(call_id: int, client_name: str, bi: dict, negotiation: dict) -> None:
    from ..db import SessionLocal

    db = SessionLocal()
    try:
        call = db.get(Call, call_id)
        if not call:
            return
        call.status = "running"
        db.commit()

        async def write(line) -> None:
            # fresh session per write: background thread owns it
            nonlocal call
            if call not in db:
                call = db.get(Call, call_id)
            db.add(
                TranscriptLine(
                    call_id=call_id,
                    role=line.role,
                    text=line.text,
                    stage=line.stage,
                    emotion=line.emotion,
                    confidence=line.confidence,
                )
            )
            call.stage = line.stage
            db.commit()

        outcome, duration_s, sentiment = asyncio.run(replay_call(client_name, bi, write, negotiation))
        call.status = "done"
        call.outcome = outcome
        call.duration_s = duration_s
        call.sentiment = sentiment
        db.commit()
        auto_book_meeting(db, call.client_id, call.id, outcome)
        create_followups(db, call.client_id, call.id, outcome, bi.get("recommended_service"))
        extract_from_call(db, call.id)
        review_and_store(db, call.id)
    finally:
        db.close()


@router.post("", response_model=CallOut, status_code=201)
def start_call(
    client_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
):
    client = _get_client(client_id, db)

    running = (
        db.query(Call)
        .filter(Call.client_id == client_id, Call.status == "running")
        .first()
    )
    if running:
        raise HTTPException(status_code=409, detail="A call is already in progress")

    call = Call(client_id=client_id, status="running", stage=STAGES[0])
    db.add(call)
    db.commit()
    db.refresh(call)

    bi = _bi_for(db, client_id)
    negotiation = _negotiation_for(db, client_id)
    background.add_task(_replay_and_save, call.id, client.name, bi, negotiation)
    return call


@router.get("", response_model=list[CallOut])
def list_calls(client_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    _get_client(client_id, db)
    return (
        db.query(Call)
        .filter(Call.client_id == client_id)
        .order_by(Call.created_at.desc())
        .all()
    )


@router.get("/{call_id}", response_model=CallDetail)
def get_call(client_id: int, call_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    _get_client(client_id, db)
    call = db.get(Call, call_id)
    if not call or call.client_id != client_id:
        raise HTTPException(status_code=404, detail="Call not found")
    return call
