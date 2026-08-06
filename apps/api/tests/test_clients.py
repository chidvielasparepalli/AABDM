def test_create_client(client):
    r = client.post("/clients", json={"name": "Test Co", "industry": "ecommerce"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Test Co"
    assert body["status"] == "Lead"


def test_list_clients_paginated(client, sample_client):
    r = client.get("/clients?limit=1&offset=0")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_client_404(client):
    r = client.get("/clients/99999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "http_error"


def test_update_client(client, sample_client):
    r = client.patch(f"/clients/{sample_client['id']}", json={"budget": 9999})
    assert r.status_code == 200
    assert r.json()["budget"] == 9999


def test_delete_client(client, sample_client):
    r = client.delete(f"/clients/{sample_client['id']}")
    assert r.status_code == 204
    assert client.get(f"/clients/{sample_client['id']}").status_code == 404


def test_client_timeline(client, sample_client):
    r = client.post(f"/clients/{sample_client['id']}/timeline", json={"event": "First touch"})
    assert r.status_code == 201
    assert r.json()["event"] == "First touch"


def test_client_email(client, sample_client):
    r = client.post(
        f"/clients/{sample_client['id']}/emails",
        json={"subject": "Hello", "body": "Body", "direction": "out"},
    )
    assert r.status_code == 201
    assert r.json()["subject"] == "Hello"


def test_client_detail_includes_relations(client, sample_client):
    r = client.get(f"/clients/{sample_client['id']}")
    assert r.status_code == 200
    body = r.json()
    for key in ("calls", "timeline", "documents", "emails"):
        assert key in body
