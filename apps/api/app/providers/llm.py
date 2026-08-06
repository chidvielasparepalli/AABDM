"""LLM provider interface.

The abstraction over every generative step: completion (chat/generation),
embedding (for KB + memory retrieval), and structured extraction.

Backward-compat contract: the default adapter is a no-op that returns None —
callers must fall back to their rule-based path. An LLM outage or a missing
key never breaks the pipeline; it only makes the output dumber.
"""

from typing import Protocol, runtime_checkable

from .common import Capability


@runtime_checkable
class LLMProvider(Capability, Protocol):
    def complete(self, prompt: str, *, model: str | None = None, max_tokens: int | None = None,
                 temperature: float | None = None, json_mode: bool = False) -> str | None:
        """Run a chat/generation completion.

        Returns the text, or None when the provider is unavailable/disabled
        (callers fall back to rule-based logic). Raises ProviderError only
        on a hard failure the caller must surface.
        """
        ...

    def embed(self, text: str, *, model: str | None = None) -> list[float] | None:
        """Embed a chunk for vector retrieval. None when disabled/unavailable."""
        ...

    def model(self) -> str:
        """Return the active model id (config-resolved)."""
        ...
