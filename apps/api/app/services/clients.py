"""ClientService — client CRUD, timeline, emails."""

from fastapi import HTTPException

from ..domain.enums import ClientStatus
from ..repositories import ClientRepository, EmailRepository, TimelineRepository
from .base import Service


class ClientService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.timeline = TimelineRepository(db, org_id)
        self.emails = EmailRepository(db, org_id)

    def list(self, limit: int, offset: int):
        return self.clients.list(limit, offset)

    def create(self, data: dict):
        if data.get("status") is None:
            data["status"] = ClientStatus.LEAD
        client = self.clients.add(**data)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get(self, client_id: int):
        client = self.clients.get(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

    def update(self, client_id: int, data: dict):
        client = self.get(client_id)
        for field, value in data.items():
            setattr(client, field, value)
        self.db.commit()
        self.db.refresh(client)
        return client

    def delete(self, client_id: int):
        client = self.get(client_id)
        self.db.delete(client)
        self.db.commit()

    def add_timeline(self, client_id: int, event: str):
        self.get(client_id)
        obj = self.timeline.add_for_client(client_id, event)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def add_email(self, client_id: int, data: dict):
        self.get(client_id)
        obj = self.emails.add_for_client(client_id, **data)
        self.db.commit()
        self.db.refresh(obj)
        return obj
