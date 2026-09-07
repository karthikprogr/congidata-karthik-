"""Config routes - admin-only, update .env settings at runtime."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import require_admin
import os, pathlib

router = APIRouter(prefix="/config", tags=["Config"])

ENV_PATH = pathlib.Path(__file__).resolve().parents[3] / ".env"


class SMTPConfig(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    admin_email: str = ""
    alert_enabled: bool = False


class OAuthConfig(BaseModel):
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""


def _read_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _write_env(updates: dict) -> None:
    env = _read_env()
    env.update(updates)
    lines = []
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.strip().startswith("#") or "=" not in line:
                lines.append(line)
                continue
            k = line.split("=")[0].strip()
            if k in env:
                lines.append(f"{k}={env.pop(k)}")
            else:
                lines.append(line)
    for k, v in env.items():
        lines.append(f"{k}={v}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


@router.get("/smtp/diagnose")
def diagnose_smtp(_: dict = Depends(require_admin)):
    """Live SMTP diagnostic - reads fresh from .env, shows exactly what will be used."""
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    host     = os.environ.get("SMTP_HOST", "")
    port     = os.environ.get("SMTP_PORT", "587")
    user     = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    admin    = os.environ.get("ADMIN_EMAIL", "")
    enabled  = os.environ.get("ALERT_EMAIL_ENABLED", "false")

    issues = []
    if not host:
        issues.append("SMTP_HOST is empty")
    elif "@" in host:
        issues.append(f"SMTP_HOST looks like an email address ('{host}') - should be 'smtp.gmail.com'")
    if not user:
        issues.append("SMTP_USER is empty")
    if not password:
        issues.append("SMTP_PASSWORD is empty")
    elif len(password.replace(" ", "")) != 16:
        issues.append(f"SMTP_PASSWORD length is {len(password.replace(' ', ''))} - Gmail App Passwords are exactly 16 chars (no spaces)")
    if not admin:
        issues.append("ADMIN_EMAIL is empty - notifications have nowhere to go")
    if enabled.lower() != "true":
        issues.append("ALERT_EMAIL_ENABLED is not 'true' - emails are disabled")

    # Try actual TCP connection
    connection_ok = False
    connection_error = ""
    try:
        import socket
        s = socket.create_connection((host, int(port)), timeout=5)
        s.close()
        connection_ok = True
    except Exception as e:
        connection_error = str(e)
        issues.append(f"Cannot reach {host}:{port} - {e}")

    return {
        "config": {
            "SMTP_HOST": host,
            "SMTP_PORT": port,
            "SMTP_USER": user,
            "SMTP_PASSWORD": "***" if password else "(empty)",
            "ADMIN_EMAIL": admin,
            "ALERT_EMAIL_ENABLED": enabled,
        },
        "issues": issues,
        "connection_ok": connection_ok,
        "connection_error": connection_error,
        "ready": len(issues) == 0 and connection_ok,
    }


@router.post("/smtp/send-test")
def send_test_now(_: dict = Depends(require_admin)):
    """Send a real test email right now using current .env config."""
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    admin = os.environ.get("ADMIN_EMAIL", "")
    if not admin:
        raise HTTPException(400, "ADMIN_EMAIL not set in .env")
    from app.services.email_service import send_test_email
    ok = send_test_email(admin)
    return {
        "success": ok,
        "sent_to": admin,
        "message": f"Test email {'sent successfully to ' + admin if ok else 'FAILED - check backend logs for SMTP error details'}",
    }
    env = _read_env()
    return {
        "smtp_host":     env.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port":     int(env.get("SMTP_PORT", "587")),
        "smtp_user":     env.get("SMTP_USER", ""),
        "smtp_password": "***" if env.get("SMTP_PASSWORD") else "",
        "admin_email":   env.get("ADMIN_EMAIL", ""),
        "alert_enabled": env.get("ALERT_EMAIL_ENABLED", "false").lower() == "true",
    }


@router.post("/smtp")
def save_smtp(data: SMTPConfig, _: dict = Depends(require_admin)):
    updates = {
        "SMTP_HOST":            data.smtp_host,
        "SMTP_PORT":            str(data.smtp_port),
        "SMTP_USER":            data.smtp_user,
        "ADMIN_EMAIL":          data.admin_email,
        "ALERT_EMAIL_ENABLED":  "true" if data.alert_enabled else "false",
    }
    if data.smtp_password and data.smtp_password != "***":
        updates["SMTP_PASSWORD"] = data.smtp_password
    _write_env(updates)
    # Reload config
    from importlib import reload
    from app.core import config
    reload(config)
    return {"message": "SMTP config saved"}


@router.post("/smtp/test")
def test_smtp(data: SMTPConfig, _: dict = Depends(require_admin)):
    """Send a test email using the provided SMTP config (without saving)."""
    from app.services.email_service import send_test_email
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    import app.core.config as cfg
    orig = {
        "SMTP_HOST": cfg.SMTP_HOST, "SMTP_PORT": cfg.SMTP_PORT,
        "SMTP_USER": cfg.SMTP_USER, "SMTP_PASSWORD": cfg.SMTP_PASSWORD,
        "ADMIN_EMAIL": cfg.ADMIN_EMAIL, "ALERT_EMAIL_ENABLED": cfg.ALERT_EMAIL_ENABLED,
    }
    try:
        cfg.SMTP_HOST = data.smtp_host or cfg.SMTP_HOST
        cfg.SMTP_PORT = data.smtp_port
        cfg.SMTP_USER = data.smtp_user or cfg.SMTP_USER
        # Only override password if not masked
        if data.smtp_password and data.smtp_password != "***":
            cfg.SMTP_PASSWORD = data.smtp_password
        cfg.ADMIN_EMAIL = data.admin_email or cfg.ADMIN_EMAIL
        cfg.ALERT_EMAIL_ENABLED = True
        to = data.admin_email or cfg.ADMIN_EMAIL
        if not to:
            return {"success": False, "error": "No admin email configured"}
        ok = send_test_email(to)
        return {"success": ok, "message": f"Test email {'sent to ' + to if ok else 'failed - check server logs'}"}
    finally:
        cfg.SMTP_HOST = orig["SMTP_HOST"]; cfg.SMTP_PORT = orig["SMTP_PORT"]
        cfg.SMTP_USER = orig["SMTP_USER"]; cfg.SMTP_PASSWORD = orig["SMTP_PASSWORD"]
        cfg.ADMIN_EMAIL = orig["ADMIN_EMAIL"]; cfg.ALERT_EMAIL_ENABLED = orig["ALERT_EMAIL_ENABLED"]


@router.get("/oauth")
def get_oauth(_: dict = Depends(require_admin)):
    env = _read_env()
    return {
        "google_client_id":     env.get("GOOGLE_CLIENT_ID", ""),
        "google_client_secret": "***" if env.get("GOOGLE_CLIENT_SECRET") else "",
        "github_client_id":     env.get("GITHUB_CLIENT_ID", ""),
        "github_client_secret": "***" if env.get("GITHUB_CLIENT_SECRET") else "",
    }


@router.post("/oauth")
def save_oauth(data: OAuthConfig, _: dict = Depends(require_admin)):
    updates = {
        "GOOGLE_CLIENT_ID":     data.google_client_id,
        "GITHUB_CLIENT_ID":     data.github_client_id,
    }
    if data.google_client_secret and data.google_client_secret != "***":
        updates["GOOGLE_CLIENT_SECRET"] = data.google_client_secret
    if data.github_client_secret and data.github_client_secret != "***":
        updates["GITHUB_CLIENT_SECRET"] = data.github_client_secret
    _write_env(updates)
    from importlib import reload
    from app.core import config
    reload(config)
    return {"message": "OAuth config saved"}


class KeysConfig(BaseModel):
    openai_key: str = ""
    aiml_key: str = ""
    aiml_model: str = ""

@router.post("/keys")
def save_keys(data: KeysConfig, _: dict = Depends(require_admin)):
    """Save API keys to .env (admin only)."""
    updates = {}
    if data.openai_key:
        updates["OPENAI_API_KEY"] = data.openai_key
        import os; os.environ["OPENAI_API_KEY"] = data.openai_key
    if data.aiml_key:
        updates["AIML_API_KEY"] = data.aiml_key
    if updates:
        _write_env(updates)
    return {"message": "Keys saved"}
