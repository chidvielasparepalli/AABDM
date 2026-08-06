import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Must be set BEFORE app import — auth.py raises if missing
os.environ.setdefault("CLERK_PUBLISHABLE_KEY", "pk_test_dGVzdC5jbGVyay5hY2NvdW50cy5kZXYk")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("AUTO_MIGRATE", "false")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth import get_current_user
from app.db import Base, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _override_auth():
    """Stub Clerk auth — no JWKS network fetch in tests."""
    async def fake_user():
        return {"sub": "test-user-123", "claims": {"sub": "test-user-123"}}

    app.dependency_overrides[get_current_user] = fake_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sample_client(client) -> dict:
    resp = client.post("/clients", json={"name": "Acme Corp", "industry": "technology", "budget": 5000})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()
