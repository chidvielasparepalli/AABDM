"""Email provider interface.

Idempotency contract: `send` is safe to retry — pass the same
`dedupe_key` and the adapter dedupes (provider message id) or the caller
checks status first. Follow-ups must never double-send on a retry.
"""

from typing import Protocol, runtime_checkable

from .common import Capability, ProviderResult


@runtime_checkable
class EmailProvider(Capability, Protocol):
    def send(self, to: str, subject: str, body: str, *, dedupe_key: str | None = None) -> ProviderResult:
        """Send an email. Returns ProviderResult (ok + message id)."""
        ...

    def get_status(self, message_id: str) -> str:
        """Return 'sent' | 'delivered' | 'failed' | 'pending'."""
        ...
