"""Memory repo."""

from ..models import Memory
from .base import ModelRepository


class MemoryRepository(ModelRepository[Memory]):
    model = Memory

    def list_for_client(self, client_id: int, limit: int, offset: int) -> list[Memory]:
        return (
            self._base()
            .filter(Memory.client_id == client_id)
            .order_by(Memory.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def all_for_client(self, client_id: int) -> list[Memory]:
        return self._base().filter(Memory.client_id == client_id).all()

    def create_from_call(self, client_id: int, key: str, value: str, source: str) -> Memory:
        return self.add(client_id=client_id, key=key, value=value, source=source)
