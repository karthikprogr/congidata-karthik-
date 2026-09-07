"""
Email service — rebuilt from scratch.
Reads credentials fresh from .env on every call.
No thread caching, no stale config.
"""
import os
import smtplib
import logging
import pathlib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

_ENV_PATH = pathlib.Path(__file__).resolve().parents[2] / ".env"


def _load_cfg() -> dict:
    """Read SMTP config fresh from .env file every single call."""
    env = {}
    try:
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    except Exception as e:
        logger.error("Failed to read .env: %s", e)
    return {
        "host":     env.get("SMTP_HOST", "smtp.gmail.com"),
        "port":     int(env.get("SMTP_PORT", "587")),
        "user":     env.get("SMTP_USER", ""),
        "password": env.get("SMTP_PASSWORD", ""),
        "admin":    env.get("ADMIN_EMAIL", ""),
        "enabled":  env.get("ALERT_EMAIL_ENABLED", "false").lower() == "true",
    }


def _send(to: str, subject: str, html_body: str) -> bool:
    """Send email synchronously. Returns True on success."""
    cfg = _load_cfg()

    if not cfg["enabled"]:
        logger.info("SMTP disabled — skipping '%s' to %s", subject, to)
        return False
    if not cfg["user"]:
        logger.error("SMTP_USER not set in .env")
        return False
    if not cfg["password"]:
        logger.error("SMTP_PASSWORD not set in .env")
        return False
    if not cfg["host"]:
        logger.error("SMTP_HOST not set in .env")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"COGNIDATA <{cfg['user']}>"
        msg["To"]      = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as srv:
            srv.ehlo()
            srv.starttls()
            srv.ehlo()
            srv.login(cfg["user"], cfg["password"])
            srv.sendmail(cfg["user"], [to], msg.as_string())

        logger.info("✅ Email sent: '%s' → %s", subject, to)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error("❌ SMTP auth failed — wrong App Password: %s", e)
    except smtplib.SMTPConnectError as e:
        logger.error("❌ SMTP connect failed (%s:%s): %s", cfg["host"], cfg["port"], e)
    except Exception as e:
        logger.error("❌ Email error (%s): %s", type(e).__name__, e)
    return False


def _send_to_admin(subject: str, html_body: str) -> bool:
    """Send to ADMIN_EMAIL. Returns True on success."""
    cfg = _load_cfg()
    admin = cfg["admin"]
    if not admin:
        logger.warning("ADMIN_EMAIL not set — cannot send admin notification")
        return False
    return _send(admin, subject, html_body)


def _send_async(to: str, subject: str, html_body: str) -> None:
    """Fire-and-forget in a daemon thread."""
    import threading
    threading.Thread(
        target=_send,
        args=(to, subject, html_body),
        daemon=True
    ).start()


def _send_to_admin_async(subject: str, html_body: str) -> None:
    import threading
    threading.Thread(
        target=_send_to_admin,
        args=(subject, html_body),
        daemon=True
    ).start()


# ── HTML template ─────────────────────────────────────────────────────────────

def _wrap(title: str, body: str, color: str = "#6366f1") -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#09090b;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px;background:#09090b">
<tr><td align="center">
<table width="520" cellpadding="0" cellspacing="0" style="background:#18181b;border-radius:12px;border:1px solid rgba(255,255,255,.1)">
  <tr><td style="background:linear-gradient(135deg,{color},#8b5cf6);padding:24px 32px;border-radius:12px 12px 0 0">
    <h1 style="margin:0;color:#fff;font-size:20px;font-weight:700">🧠 COGNIDATA</h1>
    <p style="margin:4px 0 0;color:rgba(255,255,255,.8);font-size:13px">{title}</p>
  </td></tr>
  <tr><td style="padding:28px 32px;color:#e4e4e7">{body}</td></tr>
  <tr><td style="padding:12px 32px 20px;border-top:1px solid rgba(255,255,255,.06)">
    <p style="margin:0;color:#52525b;font-size:11px">Automated message from COGNIDATA. Do not reply.</p>
  </td></tr>
</table></td></tr></table>
</body></html>"""


def _row(label: str, value: str) -> str:
    return f'<tr><td style="padding:6px 0;color:#71717a;font-size:13px;width:130px">{label}</td><td style="padding:6px 0;color:#e4e4e7;font-size:13px;font-weight:500">{value}</td></tr>'


# ── Public API ────────────────────────────────────────────────────────────────

def send_async(to: str, subject: str, body: str, html: bool = True,
               attachments: list | None = None) -> None:
    """Fire-and-forget email, optionally with attachments.
    Each attachment: {"filename": str, "data": bytes, "mime": str}
    """
    if attachments:
        import threading
        threading.Thread(
            target=_send_with_attachments,
            args=(to, subject, body, attachments),
            daemon=True,
        ).start()
    else:
        _send_async(to, subject, body)


def _send_with_attachments(to: str, subject: str, html_body: str, attachments: list) -> bool:
    """Send email with binary attachments."""
    from email.mime.base import MIMEBase
    from email import encoders
    cfg = _load_cfg()
    if not cfg["enabled"] or not cfg["user"] or not cfg["password"]:
        return False
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"]    = f"COGNIDATA <{cfg['user']}>"
        msg["To"]      = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        for att in (attachments or []):
            part = MIMEBase("application", "octet-stream")
            part.set_payload(att["data"])
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{att["filename"]}"')
            part.add_header("Content-Type", att.get("mime", "application/octet-stream"))
            msg.attach(part)
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo()
            srv.login(cfg["user"], cfg["password"])
            srv.sendmail(cfg["user"], [to], msg.as_string())
        logger.info("✅ Email with attachments sent → %s", to)
        return True
    except Exception as e:
        logger.error("❌ Email with attachments failed: %s", e)
        return False


def alert_admin(subject: str, body: str) -> None:
    _send_to_admin_async(subject, body)


def send_test_email(to: str) -> bool:
    body = _wrap("SMTP Test", '<p style="color:#4ade80;font-size:15px">✅ SMTP is working correctly!</p>')
    return _send(to, "[COGNIDATA] SMTP Test — Success", body)


# ── Auth notifications ────────────────────────────────────────────────────────

def notify_new_user(email: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = _wrap("New User Registered", f"""
    <p style="color:#e4e4e7;margin:0 0 16px">A new user registered on COGNIDATA.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;border-top:1px solid rgba(255,255,255,.08)">
      {_row("Email", email)}{_row("Time", ts)}{_row("Event", "Registration")}
    </table>""", "#22c55e")
    _send_to_admin_async("[COGNIDATA] 🆕 New User Registered", body)


def notify_login(email: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = _wrap("User Login", f"""
    <p style="color:#e4e4e7;margin:0 0 16px">A user logged in to COGNIDATA.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;border-top:1px solid rgba(255,255,255,.08)">
      {_row("Email", email)}{_row("Time", ts)}{_row("Event", "Login")}
    </table>""", "#6366f1")
    _send_to_admin_async("[COGNIDATA] 🔐 User Login", body)


def notify_failed_login(email: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = _wrap("Failed Login Attempt", f"""
    <p style="color:#f87171;margin:0 0 16px">⚠️ Failed login attempt detected.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;border-top:1px solid rgba(255,255,255,.08)">
      {_row("Email", email)}{_row("Time", ts)}{_row("Event", "Failed Login")}
    </table>""", "#ef4444")
    _send_to_admin_async("[COGNIDATA] ⚠️ Failed Login Attempt", body)


def notify_logout(email: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = _wrap("User Logout", f"""
    <p style="color:#e4e4e7;margin:0 0 16px">A user logged out of COGNIDATA.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;border-top:1px solid rgba(255,255,255,.08)">
      {_row("Email", email)}{_row("Time", ts)}{_row("Event", "Logout")}
    </table>""", "#71717a")
    _send_to_admin_async("[COGNIDATA] 👋 User Logout", body)


def notify_oauth_login(email: str, provider: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = _wrap(f"OAuth Login via {provider.title()}", f"""
    <p style="color:#e4e4e7;margin:0 0 16px">A user logged in via OAuth.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;border-top:1px solid rgba(255,255,255,.08)">
      {_row("Email", email)}{_row("Provider", provider.title())}{_row("Time", ts)}
    </table>""", "#0ea5e9")
    _send_to_admin_async(f"[COGNIDATA] 🔗 OAuth Login ({provider.title()})", body)


# ── Workspace notifications ───────────────────────────────────────────────────

def send_invitation_email(to_email: str, workspace_name: str, role: str, token: str, frontend_url: str) -> None:
    link = f"{frontend_url}/workspaces?token={token}"
    body = _wrap(f"Invitation to '{workspace_name}'", f"""
    <p style="color:#e4e4e7;margin:0 0 16px">You've been invited to join a workspace on COGNIDATA.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;border-top:1px solid rgba(255,255,255,.08);margin-bottom:20px">
      {_row("Workspace", f"<strong style='color:#a5b4fc'>{workspace_name}</strong>")}
      {_row("Your Role", role)}
      {_row("Expires", "72 hours from now")}
    </table>
    <a href="{link}" style="display:inline-block;padding:12px 24px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">
      ✅ Accept Invitation →
    </a>
    <p style="margin:20px 0 0;color:#71717a;font-size:12px">
      Or go to <strong>Workspaces → Join via Invite</strong> and paste this token:<br>
      <code style="color:#a5f3fc;background:#0f172a;padding:4px 10px;border-radius:4px;font-size:12px;display:inline-block;margin-top:6px;letter-spacing:1px">{token}</code>
    </p>""")
    # Send synchronously so errors are visible in logs
    ok = _send(to_email, f"[COGNIDATA] You're invited to join '{workspace_name}'", body)
    if not ok:
        logger.error("Failed to send invitation email to %s", to_email)


def notify_workspace_joined(owner_email: str, joiner_email: str, workspace_name: str, role: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = _wrap("New Workspace Member", f"""
    <p style="color:#e4e4e7;margin:0 0 16px">Someone accepted your workspace invitation.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;border-top:1px solid rgba(255,255,255,.08)">
      {_row("New Member", joiner_email)}{_row("Workspace", workspace_name)}{_row("Role", role)}{_row("Time", ts)}
    </table>""", "#22c55e")
    _send_async(owner_email, f"[COGNIDATA] {joiner_email} joined '{workspace_name}'", body)


# ── Keep old names for compatibility ──────────────────────────────────────────
def _html_wrap(title: str, content: str, color: str = "#6366f1") -> str:
    return _wrap(title, content, color)


def _info_row(label: str, value: str) -> str:
    return _row(label, value)


# ── Password Reset ────────────────────────────────────────────────────────────

def send_password_reset_email(to_email: str, token: str, frontend_url: str) -> None:
    """Send a branded password reset email with a reset link button."""
    reset_link = f"{frontend_url}/reset-password?token={token}"
    body = _wrap("Password Reset Request", f"""
    <p style="color:#e4e4e7;margin:0 0 16px">We received a request to reset your COGNIDATA password.</p>
    <p style="color:#71717a;font-size:13px;margin:0 0 20px">This link expires in <strong style="color:#e4e4e7">1 hour</strong>. If you did not request a reset, you can safely ignore this email.</p>
    <a href="{reset_link}" style="display:inline-block;padding:13px 28px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-radius:9px;text-decoration:none;font-weight:700;font-size:14px;letter-spacing:.02em">
      🔑 Reset My Password →
    </a>
    <p style="margin:20px 0 0;color:#52525b;font-size:11px">
      Or copy this link into your browser:<br>
      <span style="color:#a5b4fc;word-break:break-all">{reset_link}</span>
    </p>""", "#6366f1")
    _send_async(to_email, "[COGNIDATA] 🔑 Reset Your Password", body)
