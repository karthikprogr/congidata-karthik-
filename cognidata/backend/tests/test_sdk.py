"""Tests for SDK/Developer Hub endpoints."""
from tests.conftest import auth_headers, register_user
from sqlalchemy.orm import Session
from tests.conftest import TestingSessionLocal
from app.models.user import User


def make_admin(client, email="sdkadmin@example.com", password="adminpass"):
    """Register a user and promote to admin directly in DB."""
    register_user(client, email, password)
    db: Session = TestingSessionLocal()
    u = db.query(User).filter(User.email == email).first()
    if u:
        u.role = "admin"
        db.commit()
    db.close()
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestSDKReference:
    def test_get_api_reference(self, client):
        headers = make_admin(client, "sdk1@example.com")
        r = client.get("/api/sdk/reference", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "endpoints" in data
        assert "python_sdk" in data
        assert "curl_examples" in data
        assert "rate_limits" in data

    def test_reference_has_auth_endpoints(self, client):
        headers = make_admin(client, "sdk2@example.com")
        r = client.get("/api/sdk/reference", headers=headers)
        endpoints = r.json()["endpoints"]
        assert "auth" in endpoints
        assert len(endpoints["auth"]) > 0

    def test_reference_has_data_endpoints(self, client):
        headers = make_admin(client, "sdk3@example.com")
        r = client.get("/api/sdk/reference", headers=headers)
        endpoints = r.json()["endpoints"]
        assert "data" in endpoints

    def test_reference_unauthenticated(self, client):
        r = client.get("/api/sdk/reference")
        assert r.status_code == 401

    def test_quickstart_public(self, client):
        """Quickstart now requires admin role."""
        headers = make_admin(client, "sdk_qs@example.com")
        r = client.get("/api/sdk/quickstart", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "steps" in data
        assert len(data["steps"]) >= 5

    def test_quickstart_unauthenticated(self, client):
        """Quickstart should return 401 without auth."""
        r = client.get("/api/sdk/quickstart")
        assert r.status_code == 401

    def test_quickstart_has_login_step(self, client):
        headers = make_admin(client, "sdk_qs2@example.com")
        r = client.get("/api/sdk/quickstart", headers=headers)
        steps = r.json()["steps"]
        paths = [s["path"] for s in steps]
        assert "/api/auth/login" in paths

    def test_webhook_guide(self, client):
        headers = make_admin(client, "sdk4@example.com")
        r = client.get("/api/sdk/webhooks", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "setup" in data
        assert "payload_example" in data

    def test_python_sdk_contains_code(self, client):
        headers = make_admin(client, "sdk5@example.com")
        r = client.get("/api/sdk/reference", headers=headers)
        python_sdk = r.json()["python_sdk"]
        assert "import requests" in python_sdk
        assert "access_token" in python_sdk

    def test_js_sdk_contains_code(self, client):
        headers = make_admin(client, "sdk6@example.com")
        r = client.get("/api/sdk/reference", headers=headers)
        js_sdk = r.json()["javascript_sdk"]
        assert "fetch" in js_sdk
        assert "access_token" in js_sdk
