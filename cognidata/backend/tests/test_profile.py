"""Tests for profile endpoints: me, name, API keys, notifications, feedback, activity."""
import pytest
from tests.conftest import auth_headers


class TestProfileMe:
    def test_get_me(self, client):
        headers = auth_headers(client, "me@example.com")
        r = client.get("/api/profile/me", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "me@example.com"

    def test_get_me_unauthenticated(self, client):
        r = client.get("/api/profile/me")
        assert r.status_code == 401


class TestProfileName:
    def test_update_name(self, client):
        headers = auth_headers(client, "name@example.com")
        r = client.post("/api/profile/name", json={"name": "Alice"}, headers=headers)
        assert r.status_code == 200

    def test_update_name_unauthenticated(self, client):
        r = client.post("/api/profile/name", json={"name": "Alice"})
        assert r.status_code == 401


class TestAPIKeys:
    def test_list_api_keys_empty(self, client):
        headers = auth_headers(client, "keys1@example.com")
        r = client.get("/api/profile/keys", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_api_key(self, client):
        headers = auth_headers(client, "keys2@example.com")
        r = client.post("/api/profile/keys", json={"name": "my-key"}, headers=headers)
        assert r.status_code in (200, 201)
        data = r.json()
        assert "key" in data or "prefix" in data

    def test_revoke_api_key(self, client):
        headers = auth_headers(client, "keys3@example.com")
        created = client.post("/api/profile/keys", json={"name": "to-revoke"}, headers=headers).json()
        prefix = created.get("prefix") or created.get("key", "")[:8]
        r = client.delete(f"/api/profile/keys/{prefix}", headers=headers)
        assert r.status_code in (200, 204)


class TestNotifications:
    def test_get_notifications(self, client):
        headers = auth_headers(client, "notif@example.com")
        r = client.get("/api/profile/notifications", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "notifications" in data
        assert "unread" in data

    def test_mark_notifications_read(self, client):
        headers = auth_headers(client, "notif2@example.com")
        r = client.post("/api/profile/notifications/read", headers=headers)
        assert r.status_code == 200


class TestFeedback:
    def test_submit_feedback(self, client):
        headers = auth_headers(client, "fb@example.com")
        r = client.post("/api/profile/feedback",
                        json={"message": "Great platform!", "rating": 5},
                        headers=headers)
        assert r.status_code in (200, 201)

    def test_submit_feedback_unauthenticated(self, client):
        r = client.post("/api/profile/feedback", json={"message": "test"})
        assert r.status_code == 401


class TestActivity:
    def test_get_activity_log(self, client):
        headers = auth_headers(client, "act@example.com")
        r = client.get("/api/profile/activity", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestDeleteAccount:
    def test_delete_account(self, client):
        headers = auth_headers(client, "del@example.com", "delpass")
        r = client.delete("/api/profile/account", headers=headers)
        assert r.status_code in (200, 204)
