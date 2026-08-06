"""Rate limiting — slowapi in-memory. Uses distinct client per test to avoid
shared limiter state crossing tests."""
from fastapi.testclient import TestClient

from app.main import app


def test_rate_limit_exceeded():
    with TestClient(app) as c:
        # hammer past the 100/min default; TestClient uses same client IP
        codes = [c.get("/health").status_code for _ in range(110)]
        assert codes[-1] == 429
