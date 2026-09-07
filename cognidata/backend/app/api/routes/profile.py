"""Profile routes - API keys, notifications, feedback, activity."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])

class KeyCreate(BaseModel):
    name: str = "default"

class FeedbackCreate(BaseModel):
    message: str
    rating: int = 5
    category: str = "general"

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# - 2FA Status -

@router.get("/2fa-status")
def get_2fa_status(user: dict = Depends(get_current_user)):
    from app.core.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == user["email"]).first()
        if not u:
            return {"enabled": False}
        return {"enabled": bool(u.totp_enabled)}
    finally:
        db.close()


# - API Keys -

@router.get("/keys")
def list_keys(user: dict = Depends(get_current_user)):
    from app.services.api_key_service import list_keys
    return list_keys(user["email"])

@router.post("/keys", status_code=201)
def create_key(req: KeyCreate, user: dict = Depends(get_current_user)):
    from app.services.api_key_service import generate
    return generate(user["email"], req.name)

@router.delete("/keys/{key_prefix}")
def revoke_key(key_prefix: str, user: dict = Depends(get_current_user)):
    from app.services.api_key_service import _keys, revoke
    # Find full key by prefix
    full_key = next((k for k in _keys if k.startswith(key_prefix[:12])), None)
    if not full_key or not revoke(full_key, user["email"]):
        raise HTTPException(404, "Key not found")
    return {"message": "Key revoked"}

# - Notifications -

@router.get("/notifications")
def get_notifications(user: dict = Depends(get_current_user)):
    from app.services.notification_service import get_all, unread_count
    return {"notifications": get_all(user["email"]), "unread": unread_count(user["email"])}

@router.post("/notifications/read")
def mark_read(user: dict = Depends(get_current_user)):
    from app.services.notification_service import mark_read
    mark_read(user["email"])
    return {"message": "All marked as read"}

# - Feedback -

@router.post("/feedback", status_code=201)
def submit_feedback(req: FeedbackCreate, user: dict = Depends(get_current_user)):
    from app.services.feedback_service import submit
    return submit(user["email"], req.message, req.rating, req.category)

# - Activity -

@router.get("/activity")
def get_activity(user: dict = Depends(get_current_user)):
    from app.services.log_service import get_logs
    logs = get_logs(limit=100)
    return [l for l in logs if l.get("user") == user["email"]]

# - Password change -

@router.post("/change-password")
def change_password(req: PasswordChange, user: dict = Depends(get_current_user)):
    from app.core.database import SessionLocal
    from app.services.auth_service import get_user, authenticate
    from app.core.security import hash_password
    db = SessionLocal()
    try:
        u = authenticate(db, user["email"], req.old_password)
        if not u:
            raise HTTPException(401, "Current password is incorrect")
        u.hashed_password = hash_password(req.new_password)
        db.commit()
        return {"message": "Password changed"}
    finally:
        db.close()

# - Delete account -

@router.delete("/account", status_code=204)
def delete_account(user: dict = Depends(get_current_user)):
    from app.core.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == user["email"]).first()
        if u:
            db.delete(u)
            db.commit()
    finally:
        db.close()


class NameUpdate(BaseModel):
    name: str

@router.post("/name")
def update_name(req: NameUpdate, user: dict = Depends(get_current_user)):
    from app.core.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == user["email"]).first()
        if u:
            u.name = req.name
            db.commit()
        return {"message": "Name updated", "name": req.name}
    finally:
        db.close()

@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    from app.core.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == user["email"]).first()
        return {"email": user["email"], "role": user.get("role","user"), "name": u.name if u else None}
    finally:
        db.close()
