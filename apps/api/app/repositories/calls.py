"""Call + TranscriptLine repos."""

from ..models import Call, TranscriptLine
from .base import ModelRepository


class CallRepository(ModelRepository[Call]):
    model = Call

    def create(self, client_id: int, status: str, stage: str) -> Call:
        return self.add(client_id=client_id, status=status, stage=stage)

    def list_for_client(self, client_id: int, limit: int, offset: int) -> list[Call]:
        return (
            self._base()
            .filter(Call.client_id == client_id)
            .order_by(Call.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def find_running(self, client_id: int) -> Call | None:
        from ..domain.enums import CallStatus

        return (
            self._base()
            .filter(Call.client_id == client_id, Call.status == CallStatus.RUNNING)
            .first()
        )

    def add_transcript(self, call_id: int, **line) -> TranscriptLine:
        obj = TranscriptLine(organization_id=self.org_id, call_id=call_id, **line)
        self.db.add(obj)
        return obj
