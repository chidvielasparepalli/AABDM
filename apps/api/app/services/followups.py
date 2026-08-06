"""FollowUpService — draft from outcome, list, send."""

from fastapi import HTTPException

from ..followups import generate_followups, send_followup
from ..repositories import ClientRepository, FollowUpRepository
from .base import Service


class FollowUpService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.followups = FollowUpRepository(db, org_id)

    def create_from_outcome(self, client_id: int, call_id: int, outcome: str, service: str | None) -> None:
        """Called by the call saga on completion — creates pending follow-ups."""
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        for item in generate_followups(client.name, service, outcome):
            self.followups.create(
                client_id=client_id,
                call_id=call_id,
                kind=item["kind"],
                channel=item["channel"],
                content=item["content"],
            )
        self.db.commit()

    def list(self, client_id: int, limit: int, offset: int):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return self.followups.list_for_client(client_id, limit, offset)

    async def send(self, client_id: int, followup_id: int):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        followup = self.followups.get(followup_id)
        if not followup or followup.client_id != client_id:
            raise HTTPException(status_code=404, detail="Follow-up not found")

        to = client.email or client.phone or "unconfigured"
        followup.status = await send_followup(followup.channel, to, followup.content)
        self.db.commit()
        self.db.refresh(followup)
        return followup
