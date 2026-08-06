from unittest.mock import patch


def test_start_call_requires_client(client):
    r = client.post("/clients/999/calls")
    assert r.status_code == 404


def test_start_call_runs_in_background(client, sample_client):
    # patch background task target so no replay thread starts
    from app.services import CallService

    with patch.object(CallService, "replay_and_save"):
        r = client.post(f"/clients/{sample_client['id']}/calls")
        assert r.status_code == 201
        body = r.json()
        assert body["status"] == "running"
        CallService.replay_and_save.assert_called_once()


def test_list_calls_empty(client, sample_client):
    r = client.get(f"/clients/{sample_client['id']}/calls")
    assert r.status_code == 200
    assert r.json() == []


def test_get_call_404(client, sample_client):
    assert client.get(f"/clients/{sample_client['id']}/calls/999").status_code == 404


def test_duplicate_running_call_conflict(client, sample_client):
    from app.services import CallService

    with patch.object(CallService, "replay_and_save"):
        first = client.post(f"/clients/{sample_client['id']}/calls")
        assert first.status_code == 201
        second = client.post(f"/clients/{sample_client['id']}/calls")
        assert second.status_code == 409
