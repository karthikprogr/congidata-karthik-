"""Tests for alert rules and history."""
import pytest
from tests.conftest import auth_headers


class TestAlerts:
    def test_list_rules_empty(self, client):
        headers = auth_headers(client, "alrt1@example.com")
        r = client.get("/api/alerts/rules", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_rule(self, client):
        headers = auth_headers(client, "alrt2@example.com")
        r = client.post("/api/alerts/rules", json={
            "metric": "salary",
            "condition": "gt",
            "threshold": 100000,
            "message": "High salary alert",
        }, headers=headers)
        assert r.status_code in (200, 201)

    def test_delete_rule(self, client):
        headers = auth_headers(client, "alrt3@example.com")
        created = client.post("/api/alerts/rules", json={
            "metric": "age",
            "condition": "lt",
            "threshold": 18,
        }, headers=headers).json()
        rule_id = created.get("id")
        if rule_id:
            r = client.delete(f"/api/alerts/rules/{rule_id}", headers=headers)
            assert r.status_code in (200, 204)

    def test_get_alert_history(self, client):
        headers = auth_headers(client, "alrt4@example.com")
        r = client.get("/api/alerts/history", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "alerts" in data
        assert "total" in data

    def test_clear_alert_history(self, client):
        headers = auth_headers(client, "alrt5@example.com")
        r = client.delete("/api/alerts/history", headers=headers)
        assert r.status_code in (200, 204)

    def test_check_alerts_no_data(self, client):
        headers = auth_headers(client, "alrt6@example.com")
        r = client.post("/api/alerts/check", json={}, headers=headers)
        assert r.status_code in (200, 400, 404)

    def test_alerts_unauthenticated(self, client):
        r = client.get("/api/alerts/rules")
        assert r.status_code == 401
