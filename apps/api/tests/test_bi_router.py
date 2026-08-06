from app.db import SessionLocal
from app.models import ResearchReport


def _seed_report(db, client_id, status="done", seo=40, perf=30):
    db.add(
        ResearchReport(
            organization_id=1,
            client_id=client_id,
            url="https://acme.com",
            status=status,
            seo_score=seo,
            performance_score=perf,
            tech_stack=["WordPress"],
            missing_features=["Live chat widget"],
            opportunities=["Add live chat widget"],
            competitors=[],
        )
    )
    db.commit()


def test_bi_404(client):
    assert client.get("/clients/999/bi").status_code == 404


def test_bi_409_no_report(client, sample_client):
    assert client.get(f"/clients/{sample_client['id']}/bi").status_code == 409


def test_bi_409_incomplete(client, sample_client):
    with SessionLocal() as db:
        _seed_report(db, sample_client["id"], status="running")
    assert client.get(f"/clients/{sample_client['id']}/bi").status_code == 409


def test_bi_ok(client, sample_client):
    with SessionLocal() as db:
        _seed_report(db, sample_client["id"], status="done")
    r = client.get(f"/clients/{sample_client['id']}/bi")
    assert r.status_code == 200
    body = r.json()
    assert body["opportunity_score"] > 50  # gaps detected
    assert "swot" in body and "profile" in body
