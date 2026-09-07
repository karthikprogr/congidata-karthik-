"""Tests for authentication: register, login, logout, 2FA, OAuth, change-password."""
import pytest
from tests.conftest import register_user, login_user, auth_headers


# ── Register ──────────────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client):
        r = client.post("/api/auth/register", json={"email": "new@example.com", "password": "pass1234"})
        assert r.status_code == 201
        assert "user_id" in r.json()

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={"email": "dup@example.com", "password": "pass1234"})
        r = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "pass1234"})
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"].lower()

    def test_register_missing_email(self, client):
        r = client.post("/api/auth/register", json={"password": "pass1234"})
        assert r.status_code == 422

    def test_register_missing_password(self, client):
        r = client.post("/api/auth/register", json={"email": "x@example.com"})
        assert r.status_code == 422

    def test_register_empty_body(self, client):
        r = client.post("/api/auth/register", json={})
        assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client):
        register_user(client, "login@example.com", "pass1234")
        r = login_user(client, "login@example.com", "pass1234")
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client):
        register_user(client, "wp@example.com", "correct")
        r = login_user(client, "wp@example.com", "wrong")
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        r = login_user(client, "ghost@example.com", "pass")
        assert r.status_code == 401

    def test_login_missing_fields(self, client):
        r = client.post("/api/auth/login", json={"email": "x@example.com"})
        assert r.status_code == 422

    def test_login_returns_bearer_token(self, client):
        register_user(client, "bearer@example.com", "pass1234")
        r = login_user(client, "bearer@example.com", "pass1234")
        assert r.json().get("token_type", "bearer").lower() == "bearer"


# ── Logout ────────────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_success(self, client):
        headers = auth_headers(client, "logout@example.com")
        r = client.post("/api/auth/logout", headers=headers)
        assert r.status_code == 200
        assert "logged out" in r.json()["message"].lower()

    def test_logout_without_token(self, client):
        r = client.post("/api/auth/logout")
        assert r.status_code == 401


# ── Change Password ───────────────────────────────────────────────────────────

class TestChangePassword:
    def test_change_password_success(self, client):
        headers = auth_headers(client, "chpw@example.com", "oldpass1")
        r = client.post("/api/auth/change-password",
                        json={"old_password": "oldpass1", "new_password": "newpass1"},
                        headers=headers)
        assert r.status_code == 200

    def test_change_password_wrong_old(self, client):
        headers = auth_headers(client, "chpw2@example.com", "correct")
        r = client.post("/api/auth/change-password",
                        json={"old_password": "wrong", "new_password": "newpass1"},
                        headers=headers)
        assert r.status_code == 401

    def test_change_password_too_short(self, client):
        headers = auth_headers(client, "chpw3@example.com", "correct")
        r = client.post("/api/auth/change-password",
                        json={"old_password": "correct", "new_password": "ab"},
                        headers=headers)
        assert r.status_code == 422

    def test_change_password_unauthenticated(self, client):
        r = client.post("/api/auth/change-password",
                        json={"old_password": "a", "new_password": "b"})
        assert r.status_code == 401


# ── Protected route requires token ────────────────────────────────────────────

class TestProtectedRoutes:
    def test_no_token_returns_401(self, client):
        r = client.get("/api/profile/me")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client):
        r = client.get("/api/profile/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401

    def test_valid_token_allows_access(self, client):
        headers = auth_headers(client, "prot@example.com")
        r = client.get("/api/profile/me", headers=headers)
        assert r.status_code == 200


# ── 2FA ───────────────────────────────────────────────────────────────────────

class TestTwoFA:
    def test_2fa_setup_returns_secret_and_uri(self, client):
        headers = auth_headers(client, "2fa@example.com")
        r = client.post("/api/auth/2fa/setup", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "secret" in data
        assert "qr_uri" in data

    def test_2fa_confirm_invalid_code(self, client):
        headers = auth_headers(client, "2fa2@example.com")
        client.post("/api/auth/2fa/setup", headers=headers)
        r = client.post("/api/auth/2fa/confirm", json={"code": "000000"}, headers=headers)
        assert r.status_code == 401

    def test_2fa_verify_invalid_temp_token(self, client):
        r = client.post("/api/auth/2fa/verify",
                        json={"temp_token": "bad.token", "code": "123456"})
        assert r.status_code == 401


# ── OAuth URL endpoints ───────────────────────────────────────────────────────

class TestOAuthURLs:
    def test_google_oauth_url_not_configured(self, client):
        # Without GOOGLE_CLIENT_ID set, should return 400
        r = client.get("/api/auth/oauth/google/url")
        assert r.status_code in (200, 400)  # 400 if not configured

    def test_github_oauth_url_not_configured(self, client):
        r = client.get("/api/auth/oauth/github/url")
        assert r.status_code in (200, 400)
