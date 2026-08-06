from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..learning import review_call
from ..repositories import CallRepository, LearningEntryRepository
from ..schemas import LearningEntryOut, LearningStats
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/learning", tags=["learning"])


def review_and_store(db: Session, org_id: int, call_id: int) -> None:
    """Called by the call engine on completion — stores the review."""
    call = CallRepository(db, org_id).get(call_id)
    if not call or not call.transcript:
        return
    if LearningEntryRepository(db, org_id).for_call(call_id):
        return  # already reviewed

    client_lines = [t.text for t in call.transcript if t.role == "client"]
    review = review_call(client_lines, call.outcome, call.sentiment)
    LearningEntryRepository(db, org_id).create(
        call_id=call_id,
        client_id=call.client_id,
        outcome=call.outcome,
        **review,
    )
    db.commit()


@router.get("", response_model=list[LearningEntryOut])
def list_entries(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    return LearningEntryRepository(db, org_id).list(limit, offset)


@router.get("/stats", response_model=LearningStats)
def stats(
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    entries = LearningEntryRepository(db, org_id).all()
    if not entries:
        return LearningStats(total_reviews=0, avg_score=0, top_objections=[], strategies=[])

    objections = Counter(e.objection for e in entries if e.objection)
    strategies = Counter(e.strategy_used for e in entries if e.strategy_used)
    return LearningStats(
        total_reviews=len(entries),
        avg_score=round(sum(e.success_score or 0 for e in entries) / len(entries)),
        top_objections=[{"objection": k, "count": v} for k, v in objections.most_common()],
        strategies=[{"strategy": k, "count": v} for k, v in strategies.most_common()],
    )
