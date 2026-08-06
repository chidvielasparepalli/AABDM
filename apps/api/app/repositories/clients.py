"""Client-scoped repos: Client, TimelineEvent, Email."""

from ..models import Client, Email, TimelineEvent
from .base import ModelRepository


class ClientRepository(ModelRepository[Client]):
    model = Client

    def list(self, limit: int, offset: int) -> list[Client]:
        return self._base().order_by(Client.created_at.desc()).offset(offset).limit(limit).all()


class TimelineRepository(ModelRepository[TimelineEvent]):
    model = TimelineEvent

    def add_for_client(self, client_id: int, event: str) -> TimelineEvent:
        return self.add(client_id=client_id, event=event)


class EmailRepository(ModelRepository[Email]):
    model = Email

    def add_for_client(self, client_id: int, **attrs) -> Email:
        return self.add(client_id=client_id, **attrs)
