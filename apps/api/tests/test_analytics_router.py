def test_analytics_empty(client):
    r = client.get("/analytics")
    assert r.status_code == 200
    body = r.json()
    assert body["kpis"]["total_calls"] == 0
    assert "calls_series" in body
    assert "lead_quality" in body
