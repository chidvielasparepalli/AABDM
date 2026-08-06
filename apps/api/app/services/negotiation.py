"""NegotiationService — get/update per-client negotiation config."""

from fastapi import HTTPException

from ..repositories import ClientRepository, NegotiationConfigRepository
from .base import Service


class NegotiationService(Service):
    def __init__(self, db, org_id: int):
        super().__init__(db, org_id)
        self.clients = ClientRepository(db, org_id)
        self.configs = NegotiationConfigRepository(db, org_id)

    def _client_or_404(self, client_id: int):
        if not self.clients.get(client_id):
            raise HTTPException(status_code=404, detail="Client not found")

    def get(self, client_id: int):
        self._client_or_404(client_id)
        config = self.configs.for_client(client_id)
        if not config:
            config = self.configs.add(
                client_id=client_id,
                pricing=[],
                discounts=[],
                freebies=[],
                payment_terms=[],
                escalation_rules=[],
            )
            self.db.commit()
            self.db.refresh(config)
        return config

    def update(self, client_id: int, data: dict):
        self._client_or_404(client_id)
        config = self.configs.for_client(client_id)
        if not config:
            config = self.configs.add(client_id=client_id)
            self.db.add(config)
        for field, value in data.items():
            setattr(config, field, value)
        self.db.commit()
        self.db.refresh(config)
        return config
