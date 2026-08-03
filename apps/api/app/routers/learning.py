from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..learning import review_call
from ..models import Call, LearningEntry
from ..schemas import LearningEntryOut, LearningStats

router = APIRouter(prefix="/learning", tags=["learning"])


def review_and_store(db: Session, call_id: int) -> None:
    """Called by the call engine on completion — stores the review."""
    call = db.get(Call, call_id)
    if not call or not call.transcript:
        return
    if db.query(LearningEntry).filter(LearningEntry.call_id == call_id).first():
        return  # already reviewed

    client_lines = [t.text for t in call.transcript if t.role == "client"]
    review = review_call(client_lines, call.outcome, call.sentiment)
    db.add(
        LearningEntry(
            call_id=call_id,
            client_id=call.client_id,
            outcome=call.outcome,
            **review,
        )
    )
    db.commit()


@router.get("", response_model=list[LearningEntryOut])
def list_entries(db: Session = Depends(get_db), _: dict = CurrentUser):
    return db.query(LearningEntry).order_by(LearningEntry.created_at.desc()).all()


@router.get("/stats", response_model=LearningStats)
def stats(db: Session = Depends(get_db), _: dict = CurrentUser):
    entries = db.query(LearningEntry).all()
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
