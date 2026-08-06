"""Provider interface sanity tests.

Verifies the abstraction contracts are importable and structurally sound —
no implementations yet, so these guard against breaking the interface
surface (method signatures) that adapters will implement against.
"""

from app.providers.calendar import CalendarProvider
from app.providers.common import ProviderError, ProviderResult
from app.providers.email import EmailProvider
from app.providers.llm import LLMProvider
from app.providers.research import ResearchProvider
from app.providers.storage import StorageProvider
from app.providers.voice import VoiceLine, VoiceProvider
from app.providers.whatsapp import WhatsAppProvider


def test_all_providers_are_protocols():
    for iface in (
        LLMProvider, ResearchProvider, VoiceProvider,
        EmailProvider, WhatsAppProvider, CalendarProvider, StorageProvider,
    ):
        assert isinstance(iface, type) and hasattr(iface, "_is_protocol")
        assert iface._is_protocol


def test_provider_result_helpers():
    ok = ProviderResult.success("email", data={"id": "m1"})
    assert ok.ok and ok.provider == "email" and ok.data == {"id": "m1"}

    fail = ProviderResult.failure("email", "boom")
    assert not fail.ok and "boom" in fail.data["error"]


def test_provider_error_retryable_semantics():
    assert ProviderError("email", "rate limited", retryable=True).retryable
    assert not ProviderError("email", "bad auth", retryable=False).retryable
    assert "email" in str(ProviderError("email", "boom"))


def test_voice_line_dataclass():
    line = VoiceLine(role="ai", text="Hi", stage="Greeting", confidence=0.9)
    assert line.role == "ai"
    assert line.stage == "Greeting"
    assert line.confidence == 0.9
    # defaults
    assert VoiceLine("client", "ok", "Close").emotion is None


def test_protocol_structural_typing():
    """A concrete class satisfying LLMProvider structurally is accepted."""

    class FakeLLM:
        def complete(self, prompt, *, model=None, max_tokens=None, temperature=None, json_mode=False):
            return None

        def embed(self, text, *, model=None):
            return None

        def model(self):
            return "fake"

        def health(self):
            return {"status": "ok", "latency_ms": 0}

        def cost_info(self):
            return {"currency": "USD", "unit_price": 0.0, "unit": "token"}

    fake = FakeLLM()
    assert isinstance(fake, LLMProvider)
    # Protocol's structural check is duck-typed; verify the surface exists
    for meth in ("complete", "embed", "model", "health", "cost_info"):
        assert callable(getattr(fake, meth))
