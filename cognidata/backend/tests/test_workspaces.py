"""Tests for workspace CRUD, members, and invitations."""
import pytest
from tests.conftest import auth_headers, register_user


def make_ws(client, headers, name="My Workspace", desc="Test"):
    return client.post("/api/workspaces", json={"name": name, "description": desc}, headers=headers)


# ── CRUD ──────────────────────────────────────────────────────────────────────

class TestWorkspaceCRUD:
    def test_create_workspace(self, client):
        headers = auth_headers(client, "ws1@example.com")
        r = make_ws(client, headers)
        assert r.status_code == 201
        assert r.json()["name"] == "My Workspace"

    def test_list_workspaces_empty(self, client):
        headers = auth_headers(client, "ws2@example.com")
        r = client.get("/api/workspaces", headers=headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_workspaces_after_create(self, client):
        headers = auth_headers(client, "ws3@example.com")
        make_ws(client, headers, "Alpha")
        make_ws(client, headers, "Beta")
        r = client.get("/api/workspaces", headers=headers)
        assert r.status_code == 200
        names = [w["name"] for w in r.json()]
        assert "Alpha" in names
        assert "Beta" in names

    def test_delete_workspace_owner(self, client):
        headers = auth_headers(client, "ws4@example.com")
        ws_id = make_ws(client, headers).json()["id"]
        r = client.delete(f"/api/workspaces/{ws_id}", headers=headers)
        assert r.status_code == 204

    def test_delete_workspace_not_owner(self, client):
        owner_h = auth_headers(client, "owner@example.com")
        other_h = auth_headers(client, "other@example.com")
        ws_id = make_ws(client, owner_h).json()["id"]
        r = client.delete(f"/api/workspaces/{ws_id}", headers=other_h)
        assert r.status_code == 403

    def test_delete_nonexistent_workspace(self, client):
        headers = auth_headers(client, "ws5@example.com")
        r = client.delete("/api/workspaces/99999", headers=headers)
        assert r.status_code == 404

    def test_create_workspace_unauthenticated(self, client):
        r = client.post("/api/workspaces", json={"name": "X"})
        assert r.status_code == 401


# ── Members ───────────────────────────────────────────────────────────────────

class TestWorkspaceMembers:
    def test_list_members_empty(self, client):
        headers = auth_headers(client, "mem1@example.com")
        ws_id = make_ws(client, headers).json()["id"]
        r = client.get(f"/api/workspaces/{ws_id}/members", headers=headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_remove_nonexistent_member(self, client):
        headers = auth_headers(client, "mem2@example.com")
        ws_id = make_ws(client, headers).json()["id"]
        r = client.delete(f"/api/workspaces/{ws_id}/members/99999", headers=headers)
        assert r.status_code == 204  # idempotent

    def test_remove_member_not_owner(self, client):
        owner_h = auth_headers(client, "memown@example.com")
        other_h = auth_headers(client, "memoth@example.com")
        ws_id = make_ws(client, owner_h).json()["id"]
        r = client.delete(f"/api/workspaces/{ws_id}/members/1", headers=other_h)
        assert r.status_code == 403


# ── Invitations ───────────────────────────────────────────────────────────────

class TestWorkspaceInvitations:
    def test_invite_creates_invitation(self, client):
        headers = auth_headers(client, "inv1@example.com")
        ws_id = make_ws(client, headers).json()["id"]
        r = client.post(f"/api/workspaces/{ws_id}/invite",
                        json={"email": "guest@example.com", "role": "viewer"},
                        headers=headers)
        assert r.status_code == 200
        assert "token" in r.json()

    def test_list_invitations(self, client):
        headers = auth_headers(client, "inv2@example.com")
        ws_id = make_ws(client, headers).json()["id"]
        client.post(f"/api/workspaces/{ws_id}/invite",
                    json={"email": "g@example.com", "role": "viewer"}, headers=headers)
        r = client.get(f"/api/workspaces/{ws_id}/invitations", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_revoke_invitation(self, client):
        headers = auth_headers(client, "inv3@example.com")
        ws_id = make_ws(client, headers).json()["id"]
        inv_id = client.post(f"/api/workspaces/{ws_id}/invite",
                             json={"email": "g@example.com", "role": "viewer"},
                             headers=headers).json()
        # get the invitation id
        invs = client.get(f"/api/workspaces/{ws_id}/invitations", headers=headers).json()
        inv_id = invs[0]["id"]
        r = client.delete(f"/api/workspaces/{ws_id}/invitations/{inv_id}", headers=headers)
        assert r.status_code == 204

    def test_join_workspace_valid_token(self, client):
        owner_h = auth_headers(client, "joinown@example.com")
        member_h = auth_headers(client, "joinmem@example.com")
        ws_id = make_ws(client, owner_h).json()["id"]
        token = client.post(f"/api/workspaces/{ws_id}/invite",
                            json={"email": "joinmem@example.com", "role": "viewer"},
                            headers=owner_h).json()["token"]
        r = client.post("/api/workspaces/join", json={"token": token}, headers=member_h)
        assert r.status_code == 200
        assert "joined" in r.json()["message"].lower()

    def test_join_workspace_invalid_token(self, client):
        headers = auth_headers(client, "joinbad@example.com")
        r = client.post("/api/workspaces/join", json={"token": "bad-token"}, headers=headers)
        assert r.status_code == 400

    def test_join_info_valid_token(self, client):
        owner_h = auth_headers(client, "infoown@example.com")
        ws_id = make_ws(client, owner_h).json()["id"]
        token = client.post(f"/api/workspaces/{ws_id}/invite",
                            json={"email": "x@example.com", "role": "editor"},
                            headers=owner_h).json()["token"]
        r = client.get(f"/api/workspaces/join/info?token={token}")
        assert r.status_code == 200
        assert r.json()["role"] == "editor"

    def test_join_info_invalid_token(self, client):
        r = client.get("/api/workspaces/join/info?token=invalid")
        assert r.status_code == 400

    def test_double_join_is_idempotent(self, client):
        owner_h = auth_headers(client, "dblown@example.com")
        member_h = auth_headers(client, "dblmem@example.com")
        ws_id = make_ws(client, owner_h).json()["id"]
        token = client.post(f"/api/workspaces/{ws_id}/invite",
                            json={"email": "dblmem@example.com", "role": "viewer"},
                            headers=owner_h).json()["token"]
        client.post("/api/workspaces/join", json={"token": token}, headers=member_h)
        r = client.post("/api/workspaces/join", json={"token": token}, headers=member_h)
        assert r.status_code == 400  # already used
