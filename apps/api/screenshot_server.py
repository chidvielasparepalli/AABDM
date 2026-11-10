"""Temporary dev server for UI screenshots — auth overridden to a fixed user.

Same override mechanism the test suite uses (conftest.py). Not a prod auth
bypass: this file is never shipped, deleted after screenshots.
"""
import asyncio
import os

os.environ["CLERK_PUBLISHABLE_KEY"] = "pk_test_c21pbGluZy1hbnRlbG9wZS02NzcwLmNsZXJrLmFjY291bnRzLmRldiQ"
os.environ["CLERK_SECRET_KEY"] = "sk_test_rWg2hUgNub4rMQnrIniecVx8PkgIqU9umyHRx4ikYH"
os.environ["DATABASE_URL"] = "sqlite:///./shot.db"
os.environ["AUTO_MIGRATE"] = "false"
os.environ["CORS_ORIGINS"] = '["http://localhost:3001"]'
os.environ["LOG_LEVEL"] = "DEBUG"

from app.auth import get_current_user  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Call, Client, Organization, TranscriptLine  # noqa: E402
from app.db import SessionLocal  # noqa: E402


async def fake_user():
    return {"sub": "shot-user", "claims": {"sub": "shot-user"}}


app.dependency_overrides[get_current_user] = fake_user


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        org = Organization(id=1, name="Seed Org")
        db.add(org)
        db.flush()
        for name, ind, budget in [
            ("Nova Brewing Co", "ecommerce", 4000),
            ("Blue Harbor Legal", "legal", 6000),
            ("Ferro Manufacturing", "manufacturing", 4500),
            ("Kite & Finch Studio", "technology", 8000),
        ]:
            c = Client(organization_id=1, name=name, company=name, industry=ind, budget=budget,
                       status="Lead" if budget < 5000 else "Proposal",
                       website=name.lower().replace(" ", "").replace("&", "and") + ".com")
            db.add(c)
            db.flush()
            call = Call(organization_id=1, client_id=c.id, status="done", outcome="Meeting / proposal requested",
                        sentiment="positive", duration_s=348, stage="Close")
            db.add(call)
            db.flush()
            db.add(TranscriptLine(organization_id=1, call_id=call.id, role="ai", text=f"Hi {name}, this is Ava from AABDM.",
                                  stage="Greeting", confidence=0.92))
            db.add(TranscriptLine(organization_id=1, call_id=call.id, role="client",
                                  text="That sounds interesting — what would it cost?", stage="Objection", emotion="interested"))
        db.commit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the screenshot API server.")
    parser.add_argument("--seed", action="store_true", help="Seed the database before running the server.")
    args = parser.parse_args()

    if args.seed:
        print("Seeding database...")
        seed()
        print("Database seeded.")

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
