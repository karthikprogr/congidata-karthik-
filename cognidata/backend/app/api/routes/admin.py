"""Admin routes - user management, logs, metrics, broadcast, feedback, alerts."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.services.log_service import get_logs, get_metrics, get_summary

router = APIRouter(prefix="/admin", tags=["Admin"])


class BroadcastRequest(BaseModel):
    message: str
    type: str = "info"  # info | success | warning | error


class RoleUpdate(BaseModel):
    role: str  # user | admin


class StatusUpdate(BaseModel):
    active: bool


# - Users -

@router.get("/users")
def list_users(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "role": u.role,
             "active": bool(getattr(u, "active", True)),
             "created_at": getattr(u, "created_at", None),
             "totp_enabled": bool(u.totp_enabled)} for u in users]


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.email == admin["sub"]:
        raise HTTPException(400, "Cannot delete yourself")
    db.delete(user); db.commit()


@router.patch("/users/{user_id}/role")
def change_role(user_id: int, data: RoleUpdate, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.email == admin["sub"]:
        raise HTTPException(400, "Cannot change your own role")
    if data.role not in ("user", "admin"):
        raise HTTPException(400, "Role must be 'user' or 'admin'")
    user.role = data.role
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}


@router.patch("/users/{user_id}/status")
def toggle_status(user_id: int, data: StatusUpdate, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.active = data.active
    db.commit()
    from app.services.log_service import log_event
    log_event(admin["sub"], "user_status_change", f"{user.email} - {'active' if data.active else 'inactive'}")
    return {"id": user.id, "email": user.email, "active": user.active}


# - Logs & Metrics -

@router.get("/logs")
def logs(limit: int = 100, _: dict = Depends(require_admin)):
    return get_logs(min(limit, 500))


@router.get("/metrics")
def metrics(limit: int = 200, _: dict = Depends(require_admin)):
    return get_metrics(min(limit, 500))


@router.get("/summary")
def summary(_: dict = Depends(require_admin)):
    return get_summary()


# - Broadcast -

@router.post("/broadcast")
def broadcast(data: BroadcastRequest, admin: dict = Depends(require_admin)):
    from app.services.notification_service import send
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for u in users:
            send(u.email, "- Admin Broadcast", data.message, data.type)
        from app.services.log_service import log_event
        log_event(admin["sub"], "broadcast", f"Sent to {len(users)} users: {data.message[:60]}")
        return {"sent": len(users), "type": data.type}
    finally:
        db.close()


# - Feedback -

@router.get("/feedback")
def get_feedback(_: dict = Depends(require_admin)):
    from app.services.feedback_service import get_all, get_avg_rating
    return {"feedback": get_all(), "avg_rating": get_avg_rating()}


# - Admin alerts (auth events) -

@router.get("/alerts")
def get_alerts(limit: int = 50, _: dict = Depends(require_admin)):
    """Returns recent auth events from the log as admin alerts."""
    logs = get_logs(500)
    alert_actions = {"user_login", "user_logout", "failed_login", "user_register",
                     "oauth_login", "2fa_enabled", "2fa_disabled"}
    alerts = [l for l in logs if l.get("action") in alert_actions][:limit]
    return alerts


# - System stats -

@router.get("/system")
def system_stats(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    import os, sys
    stats = {
        "users": db.query(User).count(),
        "python_version": sys.version.split()[0],
    }
    try:
        import psutil
        stats["memory_mb"] = round(psutil.Process().memory_info().rss / 1024 / 1024, 1)
        stats["cpu_percent"] = psutil.cpu_percent(interval=0.1)
    except ImportError:
        pass
    try:
        from app.core.config import DATABASE_URL
        from app.core.database import engine
        if "sqlite" in DATABASE_URL:
            db_path = DATABASE_URL.replace("sqlite:///./", "")
            if os.path.exists(db_path):
                stats["db_size_mb"] = round(os.path.getsize(db_path) / 1024 / 1024, 2)
                stats["db_type"] = "SQLite"
        elif "mysql" in DATABASE_URL:
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) "
                    "FROM information_schema.tables WHERE table_schema = DATABASE()"
                )).scalar()
                stats["db_size_mb"] = float(result or 0)
                stats["db_type"] = "MySQL"
    except Exception:
        pass
    return stats


@router.get("/ai-usage")
def ai_usage(_: dict = Depends(require_admin)):
    """AI usage statistics."""
    metrics = get_metrics(500)
    ai_metrics = [m for m in metrics if "/ai" in m.get("endpoint","") or "/ml" in m.get("endpoint","")]
    total = len(ai_metrics)
    by_endpoint = {}
    for m in ai_metrics:
        ep = m.get("endpoint","")
        by_endpoint[ep] = by_endpoint.get(ep, 0) + 1
    return {"total": total, "by_endpoint": by_endpoint, "recent": ai_metrics[:20]}


_active_sessions: dict = {}  # token -> {user, created, expires}

@router.get("/sessions")
def get_sessions(_: dict = Depends(require_admin)):
    """Get active session count (approximate from recent logins)."""
    from app.services.log_service import get_logs
    logs = get_logs(200)
    logins = [l for l in logs if l.get("action") in ("user_login","oauth_login")]
    return {"count": len(logins), "recent_logins": logins[:10]}
