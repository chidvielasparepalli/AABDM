from app.followups import generate_followups


def test_generate_positive_outcome():
    items = generate_followups("Acme", "SEO", "Meeting / proposal requested")
    kinds = {i["kind"] for i in items}
    assert kinds == {"thank_you", "portfolio"}
    assert all("Ava" in i["content"] for i in items)


def test_generate_warm_outcome():
    items = generate_followups("Acme", "SEO", "Follow-up scheduled")
    assert [i["kind"] for i in items] == ["follow_up"]


def test_generate_other_outcome_empty():
    assert generate_followups("Acme", None, "something else") == []


def test_send_followup_mock(client, sample_client):
    # create a followup directly via service then send it
    from app.db import SessionLocal
    from app.services import FollowUpService

    with SessionLocal() as db:
        FollowUpService(db, 1).create_from_outcome(sample_client["id"], 1, "Meeting / proposal requested", "SEO")

    r = client.get(f"/clients/{sample_client['id']}/follow-ups")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2

    r = client.post(f"/clients/{sample_client['id']}/follow-ups/{items[0]['id']}/send")
    assert r.status_code == 200
    assert r.json()["status"] == "sent (mock)"


def test_send_followup_404(client, sample_client):
    assert client.post(f"/clients/{sample_client['id']}/follow-ups/999/send").status_code == 404
