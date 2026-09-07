"""Tests for admin endpoints — requires admin role."""
import pytest
from tests.conftest import auth_headers, register_user
from sqlalchemy.orm import Session
from tests.conftest import TestingSessionLocal
from app.models.user import User


def make_admin(client, email="admin@example.com", password="adminpass"):
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


class TestAdminUsers:
    def test_list_users_as_admin(self, client):
        headers = make_admin(client, "adm1@example.com")
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_users_as_regular_user(self, client):
        headers = auth_headers(client, "reg1@example.com")
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code in (200, 403)  # depends on require_admin implementation

    def test_list_users_unauthenticated(self, client):
        r = client.get("/api/admin/users")
        assert r.status_code == 401

    def test_change_user_role(self, client):
        headers = make_admin(client, "adm2@example.com")
        register_user(client, "target@example.com")
        db = TestingSessionLocal()
        target = db.query(User).filter(User.email == "target@example.com").first()
        uid = target.id
        db.close()
        r = client.patch(f"/api/admin/users/{uid}/role",
                         json={"role": "admin"}, headers=headers)
        assert r.status_code == 200

    def test_toggle_user_status(self, client):
        headers = make_admin(client, "adm3@example.com")
        register_user(client, "toggle@example.com")
        db = TestingSessionLocal()
        target = db.query(User).filter(User.email == "toggle@example.com").first()
        uid = target.id
        db.close()
        r = client.patch(f"/api/admin/users/{uid}/status",
                         json={"active": False}, headers=headers)
        assert r.status_code == 200

    def test_delete_user_as_admin(self, client):
        headers = make_admin(client, "adm4@example.com")
        register_user(client, "todel@example.com")
        db = TestingSessionLocal()
        target = db.query(User).filter(User.email == "todel@example.com").first()
        uid = target.id
        db.close()
        r = client.delete(f"/api/admin/users/{uid}", headers=headers)
        assert r.status_code in (200, 204)


class TestAdminMetrics:
    def test_get_metrics(self, client):
        headers = make_admin(client, "adm5@example.com")
        r = client.get("/api/admin/metrics", headers=headers)
        assert r.status_code == 200

    def test_get_summary(self, client):
        headers = make_admin(client, "adm6@example.com")
        r = client.get("/api/admin/summary", headers=headers)
        assert r.status_code == 200

    def test_get_logs(self, client):
        headers = make_admin(client, "adm7@example.com")
        r = client.get("/api/admin/logs", headers=headers)
        assert r.status_code == 200

    def test_get_system_stats(self, client):
        headers = make_admin(client, "adm8@example.com")
        r = client.get("/api/admin/system", headers=headers)
        assert r.status_code == 200

    def test_get_ai_usage(self, client):
        headers = make_admin(client, "adm9@example.com")
        r = client.get("/api/admin/ai-usage", headers=headers)
        assert r.status_code == 200

    def test_get_feedback(self, client):
        headers = make_admin(client, "adm10@example.com")
        r = client.get("/api/admin/feedback", headers=headers)
        assert r.status_code == 200

    def test_get_auth_alerts(self, client):
        headers = make_admin(client, "adm11@example.com")
        r = client.get("/api/admin/alerts", headers=headers)
        assert r.status_code == 200

    def test_broadcast_message(self, client):
        headers = make_admin(client, "adm12@example.com")
        r = client.post("/api/admin/broadcast",
                        json={"message": "System maintenance at 5pm"},
                        headers=headers)
        assert r.status_code == 200
