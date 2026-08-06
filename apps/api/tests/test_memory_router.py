def test_memory_empty(client, sample_client):
    r = client.get(f"/clients/{sample_client['id']}/memory")
    assert r.status_code == 200
    assert r.json() == []


def test_memory_404(client):
    assert client.get("/clients/999/memory").status_code == 404
