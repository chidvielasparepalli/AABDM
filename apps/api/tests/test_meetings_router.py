def test_list_meetings_empty(client):
    r = client.get("/meetings")
    assert r.status_code == 200
    assert r.json() == []


def test_create_meeting(client, sample_client):
    r = client.post(
        "/meetings",
        json={"client_id": sample_client["id"], "title": "Discovery", "scheduled_at": "2026-08-10T10:00:00Z"},
    )
    assert r.status_code == 201
    assert r.json()["title"] == "Discovery"


def test_create_meeting_404_client(client):
    r = client.post("/meetings", json={"client_id": 999, "title": "x", "scheduled_at": "2026-08-10T10:00:00Z"})
    assert r.status_code == 404


def test_set_status_invalid(client, sample_client):
    m = client.post(
        "/meetings",
        json={"client_id": sample_client["id"], "title": "Discovery", "scheduled_at": "2026-08-10T10:00:00Z"},
    ).json()
    r = client.post(f"/meetings/{m['id']}/status", json={"status": "banana"})
    assert r.status_code == 422  # not in enum


def test_set_status_valid(client, sample_client):
    m = client.post(
        "/meetings",
        json={"client_id": sample_client["id"], "title": "Discovery", "scheduled_at": "2026-08-10T10:00:00Z"},
    ).json()
    r = client.post(f"/meetings/{m['id']}/status", json={"status": "confirmed"})
    assert r.status_code == 200
    assert r.json()["status"] == "confirmed"


def test_auto_book_meeting_on_positive(client, sample_client):
    from app.db import SessionLocal
    from app.routers.calendar import auto_book_meeting

    with SessionLocal() as db:
        meeting = auto_book_meeting(db, sample_client["id"], 1, "Meeting / proposal requested")
        assert meeting is not None
        assert meeting.status == "booked"


def test_no_auto_book_on_warm(client, sample_client):
    from app.db import SessionLocal
    from app.routers.calendar import auto_book_meeting

    with SessionLocal() as db:
        assert auto_book_meeting(db, sample_client["id"], 1, "Follow-up scheduled") is None
