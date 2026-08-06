"""LearningService — review a completed call, store the entry, aggregate stats."""

from collections import Counter

from ..learning import review_call
from ..repositories import CallRepository, LearningEntryRepository
from ..schemas import LearningStats
from .base import Service


class LearningService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.calls = CallRepository(db, org_id)
        self.entries = LearningEntryRepository(db, org_id)

    def list(self, limit: int, offset: int):
        return self.entries.list(limit, offset)

    def stats(self) -> LearningStats:
        entries = self.entries.all()
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

    def review_and_store(self, call_id: int) -> None:
        """Called by the call saga on completion — stores the review."""
        call = self.calls.get(call_id)
        if not call or not call.transcript:
            return
        if self.entries.for_call(call_id):
            return  # already reviewed

        client_lines = [t.text for t in call.transcript if t.role == "client"]
        review = review_call(client_lines, call.outcome, call.sentiment)
        self.entries.create(
            call_id=call_id,
            client_id=call.client_id,
            outcome=call.outcome,
            **review,
        )
        self.db.commit()
