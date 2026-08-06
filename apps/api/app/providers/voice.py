"""Voice provider interface.

Abstraction over call transport. The simulator adapter reproduces today's
`replay_call` (deterministic lines at a fixed pace); real adapters (Twilio,
Vapi) stream audio with STT/TTS. The `stream` contract is exactly the
`replay_call` write callback signature — business logic is transport-agnostic.
"""

from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol, runtime_checkable

from .common import Capability


@dataclass(frozen=True)
class VoiceLine:
    role: str  # 'ai' | 'client'
    text: str
    stage: str
    emotion: str | None = None
    confidence: float | None = None


@runtime_checkable
class VoiceProvider(Capability, Protocol):
    def start_call(self, client_ref: str) -> str:
        """Open a call; return a provider call handle. Raises ProviderError on failure."""
        ...

    async def stream(self, lines: list[VoiceLine], emit: Callable[[VoiceLine], Awaitable[None]]) -> dict:
        """Play lines, calling emit(line) per line for persistence + real-time.

        Returns the completed call summary {'outcome': str, 'sentiment': str,
        'duration_s': int, 'recording_url': str | None}.
        """
        ...

    def end_call(self, handle: str) -> dict:
        """Finalize; return recording/summary metadata."""
        ...

    def synthesize(self, text: str) -> bytes:
        """Text-to-speech to audio bytes. Optional for adapters that stream natively."""
        ...
