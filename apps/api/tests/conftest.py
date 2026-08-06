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
from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import Organization, OrganizationMember

TEST_USER = "test-user-123"
DEFAULT_ORG_ID = 1


@pytest.fixture(scope="session", autouse=True)
def _override_auth():
    """Stub Clerk auth — no JWKS network fetch in tests."""
    async def fake_user():
        return {"sub": TEST_USER, "claims": {"sub": TEST_USER}}

    app.dependency_overrides[get_current_user] = fake_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(_seed_orgs):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def _seed_orgs():
    """Create the default org + test orgs, and make TEST_USER a member.

    Membership matters: org-id-header requests run through get_current_org's
    membership check. Org 1 (legacy default) gets the user so no-header
    requests resolve to it.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        default = Organization(id=DEFAULT_ORG_ID, name="Default Org")
        db.add(default)
        org2 = Organization(name="Org Two")
        org3 = Organization(name="Org Three")
        org4 = Organization(name="Org Four")
        db.add_all([org2, org3, org4])
        db.flush()
        db.add_all(
            [
                OrganizationMember(organization_id=DEFAULT_ORG_ID, user_id=TEST_USER),
                OrganizationMember(organization_id=org2.id, user_id=TEST_USER),
                OrganizationMember(organization_id=org3.id, user_id=TEST_USER),
                OrganizationMember(organization_id=org4.id, user_id="other-user-456"),
            ]
        )
        db.commit()
        yield
    finally:
        db.close()


@pytest.fixture()
def sample_client(client) -> dict:
    resp = client.post("/clients", json={"name": "Acme Corp", "industry": "technology", "budget": 5000})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()
