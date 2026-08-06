"""LearningEntry repo."""

from ..models import LearningEntry
from .base import ModelRepository


class LearningEntryRepository(ModelRepository[LearningEntry]):
    model = LearningEntry

    def create(self, call_id: int, client_id: int, **attrs) -> LearningEntry:
        return self.add(call_id=call_id, client_id=client_id, **attrs)

    def list(self, limit: int, offset: int) -> list[LearningEntry]:
        return self._base().order_by(LearningEntry.created_at.desc()).offset(offset).limit(limit).all()

    def all(self) -> list[LearningEntry]:
        return self._base().all()

    def for_call(self, call_id: int) -> LearningEntry | None:
        return self._base().filter(LearningEntry.call_id == call_id).first()
