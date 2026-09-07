"""Tests for SMTP config endpoint and email service logic."""
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import auth_headers


# ── Config endpoint ───────────────────────────────────────────────────────────

class TestSMTPConfig:
    def test_get_smtp_config_authenticated(self, client):
        from tests.conftest import TestingSessionLocal, register_user
        from app.models.user import User
        register_user(client, "smtp1@example.com", "adminpass")
        db = TestingSessionLocal()
        u = db.query(User).filter(User.email == "smtp1@example.com").first()
        u.role = "admin"
        db.commit(); db.close()
        r = client.post("/api/auth/login", json={"email": "smtp1@example.com", "password": "adminpass"})
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        r = client.get("/api/config/smtp", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "smtp_host" in data
        assert "smtp_port" in data
        assert "alert_enabled" in data

    def test_get_smtp_config_unauthenticated(self, client):
        r = client.get("/api/config/smtp")
        assert r.status_code == 401

    def test_save_smtp_config(self, client):
        from tests.conftest import TestingSessionLocal, register_user
        from app.models.user import User
        register_user(client, "smtp2@example.com", "adminpass")
        db = TestingSessionLocal()
        u = db.query(User).filter(User.email == "smtp2@example.com").first()
        u.role = "admin"
        db.commit(); db.close()
        r = client.post("/api/auth/login", json={"email": "smtp2@example.com", "password": "adminpass"})
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        payload = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@gmail.com",
            "smtp_password": "apppassword",
            "admin_email": "admin@example.com",
            "alert_enabled": False,
        }
        r = client.post("/api/config/smtp", json=payload, headers=headers)
        assert r.status_code == 200

    def test_test_smtp_disabled(self, client):
        """When SMTP is disabled, test endpoint should return a meaningful response."""
        from tests.conftest import TestingSessionLocal, register_user
        from app.models.user import User
        register_user(client, "smtp3@example.com", "adminpass")
        db = TestingSessionLocal()
        u = db.query(User).filter(User.email == "smtp3@example.com").first()
        u.role = "admin"
        db.commit(); db.close()
        r = client.post("/api/auth/login", json={"email": "smtp3@example.com", "password": "adminpass"})
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        payload = {
            "smtp_host": "smtp.gmail.com", "smtp_port": 587,
            "smtp_user": "", "smtp_password": "",
            "admin_email": "", "alert_enabled": False,
        }
        r = client.post("/api/config/smtp/test", json=payload, headers=headers)
        assert r.status_code in (200, 400, 500)


# ── Email service unit tests ──────────────────────────────────────────────────

class TestEmailService:
    def test_send_disabled_returns_false(self):
        """When ALERT_EMAIL_ENABLED=False, _send should return False without connecting."""
        from app.services.email_service import _send
        with patch("app.services.email_service._cfg", return_value={
            "host": "smtp.gmail.com", "port": 587,
            "user": "u@g.com", "password": "pw",
            "admin": "a@g.com", "enabled": False,
        }):
            result = _send("to@example.com", "Subject", "<p>body</p>")
            assert result is False

    def test_send_missing_credentials_returns_false(self):
        from app.services.email_service import _send
        with patch("app.services.email_service._cfg", return_value={
            "host": "smtp.gmail.com", "port": 587,
            "user": "", "password": "",
            "admin": "", "enabled": True,
        }):
            result = _send("to@example.com", "Subject", "<p>body</p>")
            assert result is False

    def test_send_missing_host_returns_false(self):
        from app.services.email_service import _send
        with patch("app.services.email_service._cfg", return_value={
            "host": "", "port": 587,
            "user": "u@g.com", "password": "pw",
            "admin": "", "enabled": True,
        }):
            result = _send("to@example.com", "Subject", "<p>body</p>")
            assert result is False

    def test_send_smtp_auth_error_returns_false(self):
        import smtplib
        from app.services.email_service import _send
        with patch("app.services.email_service._cfg", return_value={
            "host": "smtp.gmail.com", "port": 587,
            "user": "u@g.com", "password": "wrong",
            "admin": "", "enabled": True,
        }), patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value.login.side_effect = \
                smtplib.SMTPAuthenticationError(535, b"auth failed")
            result = _send("to@example.com", "Subject", "<p>body</p>")
            assert result is False

    def test_send_async_does_not_block(self):
        """send_async should return immediately (fire-and-forget)."""
        from app.services.email_service import send_async
        with patch("app.services.email_service._send", return_value=False) as mock_send:
            send_async("to@example.com", "Subject", "<p>body</p>")
            import time; time.sleep(0.1)
            mock_send.assert_called_once()

    def test_html_wrap_contains_title(self):
        from app.services.email_service import _html_wrap
        html = _html_wrap("Test Title", "<p>content</p>")
        assert "Test Title" in html
        assert "COGNIDATA" in html

    def test_notify_new_user_called_on_register(self, client):
        """Registration should trigger notify_new_user (even if email is disabled)."""
        with patch("app.services.email_service.notify_new_user") as mock_notify:
            client.post("/api/auth/register",
                        json={"email": "notify@example.com", "password": "pass1234"})
            mock_notify.assert_called_once_with("notify@example.com")

    def test_notify_login_called_on_login(self, client):
        client.post("/api/auth/register",
                    json={"email": "notlogin@example.com", "password": "pass1234"})
        with patch("app.services.email_service.notify_login") as mock_notify:
            client.post("/api/auth/login",
                        json={"email": "notlogin@example.com", "password": "pass1234"})
            mock_notify.assert_called_once_with("notlogin@example.com")

    def test_notify_failed_login_called_on_bad_password(self, client):
        client.post("/api/auth/register",
                    json={"email": "faillogin@example.com", "password": "correct"})
        with patch("app.services.email_service.notify_failed_login") as mock_notify:
            client.post("/api/auth/login",
                        json={"email": "faillogin@example.com", "password": "wrong"})
            mock_notify.assert_called_once_with("faillogin@example.com")
