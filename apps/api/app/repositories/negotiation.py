"""NegotiationConfig repo."""

from ..models import NegotiationConfig
from .base import ModelRepository


class NegotiationConfigRepository(ModelRepository[NegotiationConfig]):
    model = NegotiationConfig

    def for_client(self, client_id: int) -> NegotiationConfig | None:
        return self._base().filter(NegotiationConfig.client_id == client_id).first()
