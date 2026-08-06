"""WhatsApp provider interface.

Same idempotency contract as email: `send` with a `dedupe_key` must not
double-deliver on retry. Supports template messages (pre-approved) and media.
"""

from typing import Protocol, runtime_checkable

from .common import Capability, ProviderResult


@runtime_checkable
class WhatsAppProvider(Capability, Protocol):
    def send(self, to: str, body: str, *, dedupe_key: str | None = None,
             template_name: str | None = None, media_url: str | None = None) -> ProviderResult:
        """Send a WhatsApp message. Returns ProviderResult (ok + message id)."""
        ...

    def get_status(self, message_id: str) -> str:
        """Return 'sent' | 'delivered' | 'failed' | 'pending'."""
        ...
