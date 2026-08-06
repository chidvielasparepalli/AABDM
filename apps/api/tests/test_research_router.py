from unittest.mock import patch


def test_research_requires_website(client):
    r = client.post("/clients/999/research")
    assert r.status_code == 404


def test_research_no_website_400(client):
    c = client.post("/clients", json={"name": "No Site Co"}).json()
    r = client.post(f"/clients/{c['id']}/research")
    assert r.status_code == 400


def test_research_latest_404(client, sample_client):
    assert client.get(f"/clients/{sample_client['id']}/research").status_code == 404


def test_research_start_runs_background(client):
    from app.routers import research as research_router

    c = client.post("/clients", json={"name": "Web Co", "website": "https://example.com"}).json()
    with patch.object(research_router, "_run_and_save"):
        r = client.post(f"/clients/{c['id']}/research")
        assert r.status_code == 201
        research_router._run_and_save.assert_called_once()
