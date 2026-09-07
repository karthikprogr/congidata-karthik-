"""Tests for Action Layer — webhook/slack/email actions."""
from tests.conftest import auth_headers


class TestActionCRUD:
    def test_list_actions_empty(self, client):
        headers = auth_headers(client, "act1@example.com")
        r = client.get("/api/actions", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_webhook_action(self, client):
        headers = auth_headers(client, "act2@example.com")
        r = client.post("/api/actions", json={
            "name": "My Webhook",
            "type": "webhook",
            "trigger": "alert",
            "url": "https://example.com/hook",
            "active": True,
        }, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "My Webhook"
        assert data["type"] == "webhook"
        assert "id" in data

    def test_create_slack_action(self, client):
        headers = auth_headers(client, "act3@example.com")
        r = client.post("/api/actions", json={
            "name": "Slack Alert",
            "type": "slack",
            "trigger": "alert",
            "url": "https://hooks.slack.com/test",
        }, headers=headers)
        assert r.status_code == 201

    def test_create_email_action(self, client):
        headers = auth_headers(client, "act4@example.com")
        r = client.post("/api/actions", json={
            "name": "Email Alert",
            "type": "email",
            "trigger": "manual",
        }, headers=headers)
        assert r.status_code == 201

    def test_list_actions_after_create(self, client):
        headers = auth_headers(client, "act5@example.com")
        client.post("/api/actions", json={"name": "W1", "type": "webhook", "trigger": "manual"}, headers=headers)
        client.post("/api/actions", json={"name": "W2", "type": "slack", "trigger": "alert"}, headers=headers)
        r = client.get("/api/actions", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_update_action(self, client):
        headers = auth_headers(client, "act6@example.com")
        created = client.post("/api/actions", json={"name": "Old", "type": "webhook", "trigger": "manual"}, headers=headers).json()
        r = client.patch(f"/api/actions/{created['id']}", json={"name": "Updated", "active": False}, headers=headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"

    def test_delete_action(self, client):
        headers = auth_headers(client, "act7@example.com")
        created = client.post("/api/actions", json={"name": "ToDelete", "type": "webhook", "trigger": "manual"}, headers=headers).json()
        r = client.delete(f"/api/actions/{created['id']}", headers=headers)
        assert r.status_code == 204

    def test_action_logs_empty(self, client):
        headers = auth_headers(client, "act8@example.com")
        r = client.get("/api/actions/logs", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_clear_action_logs(self, client):
        headers = auth_headers(client, "act9@example.com")
        r = client.delete("/api/actions/logs", headers=headers)
        assert r.status_code == 204

    def test_actions_unauthenticated(self, client):
        r = client.get("/api/actions")
        assert r.status_code == 401

    def test_run_nonexistent_action(self, client):
        headers = auth_headers(client, "act10@example.com")
        r = client.post("/api/actions/99999/run", json={}, headers=headers)
        assert r.status_code == 404


class TestActionAlertIntegration:
    def test_alert_fires_action(self, client):
        """When an alert fires, matching actions should be triggered."""
        headers = auth_headers(client, "actint@example.com")
        # Create alert rule
        client.post("/api/alerts/rules", json={
            "metric": "revenue", "condition": "lt", "threshold": 1000
        }, headers=headers)
        # Create action bound to alert
        client.post("/api/actions", json={
            "name": "Test Action", "type": "email",
            "trigger": "alert", "active": True,
        }, headers=headers)
        # Fire the alert
        r = client.post("/api/alerts/check", json={"revenue": 500}, headers=headers)
        assert r.status_code == 200
        assert r.json()["count"] >= 1
