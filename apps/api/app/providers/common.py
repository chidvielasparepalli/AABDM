"""Shared types and provider contracts."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderError(Exception):
    """A provider call failed in a way the caller can reason about.

    `retryable=True` → retry with backoff (429, timeout, 5xx).
    `retryable=False` → permanent (validation, auth, unsupported).
    """

    provider: str
    message: str
    retryable: bool = True
    detail: Any = None

    def __str__(self) -> str:
        return f"[{self.provider}] {self.message}"


@dataclass(frozen=True)
class ProviderResult:
    """Uniform success envelope for every provider call.

    Carries the idempotency key so callers can dedupe retried sends, and the
    raw provider payload for auditing.
    """

    ok: bool
    provider: str
    data: dict | None = None
    request_id: str | None = None

    @classmethod
    def success(cls, provider: str, data: dict | None = None, request_id: str | None = None) -> "ProviderResult":
        return cls(ok=True, provider=provider, data=data, request_id=request_id)

    @classmethod
    def failure(cls, provider: str, error: str, request_id: str | None = None) -> "ProviderResult":
        return cls(ok=False, provider=provider, data={"error": error}, request_id=request_id)


class Capability(Protocol):
    """Every provider adapter implements health + cost reporting."""

    def health(self) -> dict:
        """Return {'status': 'ok'|'degraded'|'down', 'latency_ms': int}."""
        ...

    def cost_info(self) -> dict:
        """Return {'currency': str, 'unit_price': float, 'unit': str} for metering."""
        ...
