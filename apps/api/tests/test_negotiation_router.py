def test_get_config_auto_creates(client, sample_client):
    r = client.get(f"/clients/{sample_client['id']}/negotiation")
    assert r.status_code == 200
    assert r.json()["pricing"] == []


def test_get_config_404(client):
    assert client.get("/clients/999/negotiation").status_code == 404


def test_update_config(client, sample_client):
    payload = {"pricing": [{"label": "Basic", "amount": 1000}]}
    r = client.put(f"/clients/{sample_client['id']}/negotiation", json=payload)
    assert r.status_code == 200
    assert r.json()["pricing"][0]["amount"] == 1000
