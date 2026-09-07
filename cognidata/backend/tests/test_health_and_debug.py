"""Tests for health check and debug endpoints."""
import pytest
from tests.conftest import auth_headers


class TestHealth:
    def test_health_check(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_debug_health(self, client):
        headers = auth_headers(client, "dbg1@example.com")
        r = client.get("/api/debug/health", headers=headers)
        assert r.status_code == 200

    def test_debug_system(self, client):
        headers = auth_headers(client, "dbg2@example.com")
        r = client.get("/api/debug/system", headers=headers)
        assert r.status_code == 200

    def test_debug_packages(self, client):
        headers = auth_headers(client, "dbg3@example.com")
        r = client.get("/api/debug/packages", headers=headers)
        assert r.status_code == 200

    def test_debug_performance(self, client):
        headers = auth_headers(client, "dbg4@example.com")
        r = client.get("/api/debug/performance", headers=headers)
        assert r.status_code == 200

    def test_debug_logs(self, client):
        headers = auth_headers(client, "dbg5@example.com")
        r = client.get("/api/debug/logs", headers=headers)
        assert r.status_code == 200

    def test_debug_traces(self, client):
        headers = auth_headers(client, "dbg6@example.com")
        r = client.get("/api/debug/traces", headers=headers)
        assert r.status_code == 200

    def test_debug_background_status(self, client):
        headers = auth_headers(client, "dbg7@example.com")
        r = client.get("/api/debug/background/status", headers=headers)
        assert r.status_code == 200

    def test_debug_watcher_events(self, client):
        headers = auth_headers(client, "dbg8@example.com")
        r = client.get("/api/debug/watcher-events", headers=headers)
        assert r.status_code == 200

    def test_debug_unauthenticated(self, client):
        r = client.get("/api/debug/system")
        assert r.status_code == 401
