"""MemoryService — list client memories, extract facts from a call."""

from fastapi import HTTPException

from ..domain.enums import MemorySource
from ..memory import extract_memories
from ..repositories import CallRepository, ClientRepository, MemoryRepository
from .base import Service


class MemoryService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.memories = MemoryRepository(db, org_id)
        self.calls = CallRepository(db, org_id)

    def list(self, client_id: int, limit: int, offset: int):
        if not self.clients.get(client_id):
            raise HTTPException(status_code=404, detail="Client not found")
        return self.memories.list_for_client(client_id, limit, offset)

    def extract_from_call(self, call_id: int) -> None:
        """After a call completes, extract and store new memories."""
        call = self.calls.get(call_id)
        if not call or not call.transcript:
            return

        existing = {m.value.lower() for m in self.memories.all_for_client(call.client_id)}
        client_lines = [t.text for t in call.transcript if t.role == "client"]
        ai_lines = [t.text for t in call.transcript if t.role == "ai"]
        facts = extract_memories(existing, client_lines, ai_lines)
        for key, value in facts:
            self.memories.create_from_call(call.client_id, key, value, MemorySource.CALL)
        self.db.commit()
