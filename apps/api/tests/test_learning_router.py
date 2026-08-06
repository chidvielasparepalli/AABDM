def test_learning_empty(client):
    r = client.get("/learning")
    assert r.status_code == 200
    assert r.json() == []


def test_learning_stats_empty(client):
    r = client.get("/learning/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_reviews"] == 0
    assert body["avg_score"] == 0


def test_learning_stats_after_review(client, sample_client):
    from app.db import SessionLocal
    from app.models import Call, TranscriptLine
    from app.routers.learning import review_and_store

    with SessionLocal() as db:
        call = Call(
            organization_id=1,
            client_id=sample_client["id"],
            status="done",
            outcome="Meeting / proposal requested",
            sentiment="positive",
        )
        db.add(call)
        db.flush()
        db.add(
            TranscriptLine(
                organization_id=1,
                call_id=call.id,
                role="client",
                text="sounds great",
                stage="Close",
            )
        )
        db.commit()
        review_and_store(db, 1, call.id)

    r = client.get("/learning/stats")
    body = r.json()
    assert body["total_reviews"] == 1
    assert body["avg_score"] >= 80
