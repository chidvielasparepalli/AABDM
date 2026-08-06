def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "x-request-id" in r.headers


def test_me(client):
    r = client.get("/me")
    assert r.status_code == 200
    assert r.json()["userId"] == "test-user-123"


def test_unknown_route(client):
    r = client.get("/nope")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert "request_id" in body["error"]


def test_validation_error_shape(client):
    r = client.post("/clients", json={})  # name required
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]
