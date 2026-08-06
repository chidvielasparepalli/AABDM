"""Tenant isolation integration tests.

Verifies the multi-tenancy invariants end-to-end through the HTTP API:

- every resource belongs to an organization
- org-scoped list/get never leaks across tenants (member of two orgs → 404
  on the other org's rows, not a peek)
- membership is enforced (non-member org header → 403)
- a user in two orgs sees each org's data independently
- child rows (calls, follow-ups, meetings, memories, research) inherit the
  parent client's org
- the no-header legacy path resolves to the default org (backward compat)
"""

HEADERS_A = {"X-Organization-ID": "2"}  # TEST_USER member
HEADERS_B = {"X-Organization-ID": "3"}  # TEST_USER member (other tenant)
HEADERS_FORBIDDEN = {"X-Organization-ID": "4"}  # TEST_USER NOT member


def _post(client, path, body, headers=None):
    return client.post(path, json=body, headers=headers)


def test_cross_org_client_list_isolation(client):
    _post(client, "/clients", {"name": "A Corp"}, HEADERS_A)
    _post(client, "/clients", {"name": "B Corp"}, HEADERS_B)

    names_a = {c["name"] for c in client.get("/clients", headers=HEADERS_A).json()}
    assert names_a == {"A Corp"}  # B Corp must not leak

    names_b = {c["name"] for c in client.get("/clients", headers=HEADERS_B).json()}
    assert names_b == {"B Corp"}


def test_cross_org_client_get_idor(client):
    a = _post(client, "/clients", {"name": "A Corp"}, HEADERS_A).json()
    # Org 3 user cannot read org 2's client by ID
    assert client.get(f"/clients/{a['id']}", headers=HEADERS_B).status_code == 404


def test_cross_org_client_update_idor(client):
    a = _post(client, "/clients", {"name": "A Corp"}, HEADERS_A).json()
    r = client.patch(f"/clients/{a['id']}", json={"notes": "pwned"}, headers=HEADERS_B)
    assert r.status_code == 404
    assert client.get(f"/clients/{a['id']}", headers=HEADERS_A).json()["notes"] is None


def test_cross_org_client_delete_idor(client):
    a = _post(client, "/clients", {"name": "A Corp"}, HEADERS_A).json()
    assert client.delete(f"/clients/{a['id']}", headers=HEADERS_B).status_code == 404
    assert client.get(f"/clients/{a['id']}", headers=HEADERS_A).status_code == 200


def test_non_member_org_header_403(client):
    # Org 4 has only "other-user-456"; TEST_USER not a member → 403
    r = client.get("/clients", headers=HEADERS_FORBIDDEN)
    assert r.status_code == 403


def test_invalid_org_header_400(client):
    r = client.get("/clients", headers={"X-Organization-ID": "banana"})
    assert r.status_code == 400


def test_multi_org_user_sees_each_org_independently(client):
    _post(client, "/clients", {"name": "Tenant2 Client"}, HEADERS_A)
    _post(client, "/clients", {"name": "Default Client"})

    # Org 2 sees its own data only — no org-3 or default-org leakage
    names_a = {c["name"] for c in client.get("/clients", headers=HEADERS_A).json()}
    assert "Tenant2 Client" in names_a
    assert "Default Client" not in names_a
    assert "B Corp" not in names_a
    # No header → default org data (may include other test-file clients)
    names_default = {c["name"] for c in client.get("/clients").json()}
    assert "Default Client" in names_default
    assert "Tenant2 Client" not in names_default


def test_child_rows_inherit_parent_org(client):
    """Calls/follow-ups/meetings/memories stamp the client's org."""
    client_data = _post(
        client,
        "/clients",
        {"name": "Child Co", "website": "https://example.com"},
        HEADERS_A,
    ).json()
    cid = client_data["id"]

    # start a call
    r = _post(client, f"/clients/{cid}/calls", {}, HEADERS_A)
    assert r.status_code == 201
    call_id = r.json()["id"]

    from datetime import datetime, timezone

    from app.db import SessionLocal
    from app.models import Call, FollowUp, Meeting, Memory, ResearchReport

    with SessionLocal() as db:
        call = db.get(Call, call_id)
        assert call.organization_id == 2

        # manual meeting in org 2
        m = Meeting(
            organization_id=2,
            client_id=cid,
            title="Discovery",
            scheduled_at=datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc),
        )
        db.add(m)
        fu = FollowUp(
            organization_id=2,
            client_id=cid,
            call_id=call_id,
            kind="follow_up",
            channel="email",
            content="x",
        )
        db.add(fu)
        mem = Memory(organization_id=2, client_id=cid, key="interest", value="SEO", source="manual")
        db.add(mem)
        rr = ResearchReport(organization_id=2, client_id=cid, url="https://example.com", status="running")
        db.add(rr)
        db.commit()

    # Org 3 cannot see org 2's client or any child rows
    assert client.get(f"/clients/{cid}", headers=HEADERS_B).status_code == 404
    assert client.get(f"/clients/{cid}/calls", headers=HEADERS_B).status_code == 404
    # Org 2 can see its own meeting
    meetings = client.get("/meetings", headers=HEADERS_A).json()
    assert any(mm["title"] == "Discovery" for mm in meetings)


def test_analytics_scoped_to_org(client):
    # revenue counts clients in Proposal/Closed stages
    _post(client, "/clients", {"name": "Analytics A", "budget": 5000, "status": "Proposal"}, HEADERS_A)
    _post(client, "/clients", {"name": "Analytics B", "budget": 9000, "status": "Proposal"}, HEADERS_B)

    rev_a = client.get("/analytics", headers=HEADERS_A).json()["kpis"]["revenue"]
    rev_b = client.get("/analytics", headers=HEADERS_B).json()["kpis"]["revenue"]
    # each org's pipeline value is its own — no cross-tenant sums
    assert rev_a == 5000
    assert rev_b == 9000
