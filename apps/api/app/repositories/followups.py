"""FollowUp repo."""

from ..models import FollowUp
from .base import ModelRepository


class FollowUpRepository(ModelRepository[FollowUp]):
    model = FollowUp

    def create(self, client_id: int, call_id: int, kind: str, channel: str, content: str) -> FollowUp:
        return self.add(client_id=client_id, call_id=call_id, kind=kind, channel=channel, content=content)

    def list_for_client(self, client_id: int, limit: int, offset: int) -> list[FollowUp]:
        return (
            self._base()
            .filter(FollowUp.client_id == client_id)
            .order_by(FollowUp.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
