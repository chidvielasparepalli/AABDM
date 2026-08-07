"""OpenAI LLM adapter — httpx only, no extra dependency.

Implements LLMProvider + Capability against the OpenAI Chat Completions and
Embeddings APIs. No API key configured → complete()/embed() return None,
preserving the backward-compat contract: an LLM outage or missing key never
breaks the pipeline, it only makes the output dumber (rule-based fallback).
"""

import httpx

from ..config import settings
from .common import ProviderError
from .llm import LLMProvider

_CHAT_URL = "https://api.openai.com/v1/chat/completions"
_EMBED_URL = "https://api.openai.com/v1/embeddings"


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
        client: httpx.Client | None = None,
    ):
        # None → fall back to settings; explicit "" forces the no-key path.
        self.api_key = settings.openai_api_key if api_key is None else api_key
        self.model = model or settings.openai_model
        self.embedding_model = embedding_model or settings.openai_embedding_model
        self._client = client or httpx.Client(timeout=30.0)

    def complete(self, prompt: str, *, model: str | None = None, max_tokens: int | None = None,
                 temperature: float | None = None, json_mode: bool = False) -> str | None:
        if not self.api_key:
            return None
        body = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        data = self._post(_CHAT_URL, body)
        # Refusal (content=None) also falls back to rule-based.
        return data["choices"][0]["message"]["content"]

    def embed(self, text: str, *, model: str | None = None) -> list[float] | None:
        if not self.api_key:
            return None
        data = self._post(_EMBED_URL, {"model": model or self.embedding_model, "input": text})
        return [d["embedding"] for d in data["data"]]

    def model(self) -> str:
        return self.model

    def health(self) -> dict:
        # ponytail: key presence is the signal, no live ping. Add a real
        # probe call when metering/uptime reporting starts.
        return {"status": "ok" if self.api_key else "down", "latency_ms": 0}

    def cost_info(self) -> dict:
        return {"currency": "USD", "unit_price": 0.15, "unit": "per-1M-input-tokens"}

    def _post(self, url: str, body: dict) -> dict:
        try:
            resp = self._client.post(url, json=body, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            retryable = exc.response.status_code in (408, 429) or exc.response.status_code >= 500
            raise ProviderError(
                "openai",
                f"HTTP {exc.response.status_code}: {exc.response.text[:500]}",
                retryable=retryable,
                detail=exc.response.text[:500],
            ) from exc
        except httpx.TransportError as exc:
            raise ProviderError("openai", f"transport: {exc}", retryable=True) from exc

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}


if __name__ == "__main__":
    """Self-check: model default, no-key → None, 429 → retryable error. No network."""
    import json

    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.read())
        if request.url.path == "/v1/chat/completions":
            return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    p = OpenAIProvider(api_key="k", client=client)

    assert p.complete("x") == "hi"
    assert seen["path"] == "/v1/chat/completions"
    assert seen["body"]["model"] == "gpt-4o-mini"  # default model applied

    settings.openai_api_key = ""  # isolate from dev env key
    assert OpenAIProvider().complete("x") is None  # no key → rule-based fallback
    assert OpenAIProvider().embed("x") is None

    try:
        p.embed("x")
        raise AssertionError("expected ProviderError on 429")
    except ProviderError as exc:
        assert exc.retryable and exc.provider == "openai"

    print("openai.py self-check OK")
