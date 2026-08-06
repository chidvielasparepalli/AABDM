"""Async research service tests — mocked HTTP."""
import pytest

from app.research import page_speed, run_research


@pytest.mark.asyncio
async def test_page_speed_non_200(monkeypatch):
    class FakeResp:
        status_code = 500
        async def json(self):
            return {}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def get(self, *a, **kw):
            return FakeResp()

    monkeypatch.setattr("app.research.httpx.AsyncClient", lambda **kw: FakeClient())
    result = await page_speed("https://example.com")
    assert result == {"score": None, "error": "PageSpeed HTTP 500"}


@pytest.mark.asyncio
async def test_run_research_success(monkeypatch):
    HTML = '<html><head><title>Acme</title></head><body>wp-content</body></html>'

    async def fake_fetch(url):
        return HTML

    async def fake_ps(url):
        return {"score": 80}

    monkeypatch.setattr("app.research.fetch_site", fake_fetch)
    monkeypatch.setattr("app.research.page_speed", fake_ps)
    report = await run_research("https://acme.com")
    assert report["status"] == "done"
    assert report["seo_score"] is not None
    assert report["performance_score"] == 80


@pytest.mark.asyncio
async def test_run_research_unreachable(monkeypatch):
    import httpx

    async def fake_fetch(url):
        raise httpx.HTTPStatusError("404", request=None, response=None)

    monkeypatch.setattr("app.research.fetch_site", fake_fetch)
    with pytest.raises(httpx.HTTPStatusError):
        await run_research("https://acme.com")
