"""Auth routes - register, login, logout, OAuth, 2FA, forgot/reset password."""
import secrets, os, httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import create_token, decode_token, hash_password
from app.core.limiter import limiter
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import authenticate, create_user, get_user, get_or_create_oauth_user
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

# - In-memory password reset token store -
# { token: {"email": str, "expires": datetime} }
_reset_tokens: dict = {}


class OAuthCallback(BaseModel):
    code: str; state: str = ""

class TwoFAVerify(BaseModel):
    temp_token: str; code: str

class TwoFAConfirm(BaseModel):
    code: str

class TwoFADisable(BaseModel):
    code: str

# - Register -

@router.post("/register", status_code=201)
@limiter.limit("5/minute")
def register(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    if get_user(db, data.email):
        raise HTTPException(400, "Email already registered")
    # Create user with default 'free' tier
    user = create_user(db, data.email, data.password, tier="free")
    try:
        from app.services.email_service import notify_new_user
        notify_new_user(data.email)
    except Exception:
        pass
    return {
        "message": "Account created",
        "user_id": user.id,
        "tier": user.tier,
        "storage_quota_mb": user.storage_quota_mb
    }

# - Login -

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, data.email, data.password)
    if not user:
        try:
            from app.services.email_service import notify_failed_login
            notify_failed_login(data.email)
        except Exception:
            pass
        raise HTTPException(401, "Invalid email or password")

    # 2FA check
    if user.totp_enabled:
        from app.utils.auth import create_user_token
        temp_token = create_token({"sub": user.email, "role": user.role, "2fa_pending": True}, expire_minutes=5)
        return {"requires_2fa": True, "temp_token": temp_token}

    # Create token with user_id, email, tier, role (Requirement 17.2)
    from app.utils.auth import create_user_token
    access_token = create_user_token(
        user_id=user.id,
        email=user.email,
        tier=user.tier,
        role=user.role
    )
    
    try:
        from app.services.email_service import notify_login
        notify_login(data.email)
    except Exception:
        pass
    
    return TokenResponse(access_token=access_token)

# - Logout -

@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    try:
        from app.services.email_service import notify_logout
        notify_logout(user["sub"])
    except Exception:
        pass
    return {"message": "Logged out"}

# - 2FA Setup -

@router.post("/2fa/setup")
def setup_2fa(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    import pyotp
    u = get_user(db, user["sub"])
    if not u: raise HTTPException(404, "User not found")
    secret = pyotp.random_base32()
    u.totp_secret = secret
    db.commit()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user["sub"], issuer_name="COGNIDATA")
    return {"secret": secret, "qr_uri": uri}

@router.post("/2fa/confirm")
def confirm_2fa(data: TwoFAConfirm, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    import pyotp
    u = get_user(db, user["sub"])
    if not u or not u.totp_secret: raise HTTPException(400, "2FA not set up")
    totp = pyotp.TOTP(u.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(401, "Invalid TOTP code")
    u.totp_enabled = True
    db.commit()
    return {"message": "2FA enabled"}

@router.post("/2fa/verify", response_model=TokenResponse)
def verify_2fa(data: TwoFAVerify, db: Session = Depends(get_db)):
    import pyotp
    try:
        payload = decode_token(data.temp_token)
    except Exception:
        raise HTTPException(401, "Invalid or expired temp token")
    if not payload.get("2fa_pending"):
        raise HTTPException(401, "Not a 2FA pending token")
    u = get_user(db, payload["sub"])
    if not u or not u.totp_secret: raise HTTPException(400, "2FA not configured")
    totp = pyotp.TOTP(u.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(401, "Invalid TOTP code")
    
    # Create token with user_id, email, tier, role (Requirement 17.2)
    from app.utils.auth import create_user_token
    access_token = create_user_token(
        user_id=u.id,
        email=u.email,
        tier=u.tier,
        role=u.role
    )
    
    try:
        from app.services.email_service import notify_login
        notify_login(u.email)
    except Exception:
        pass
    
    return TokenResponse(access_token=access_token)

@router.post("/2fa/disable")
def disable_2fa(data: TwoFADisable, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    import pyotp
    u = get_user(db, user["sub"])
    if not u or not u.totp_enabled: raise HTTPException(400, "2FA not enabled")
    totp = pyotp.TOTP(u.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(401, "Invalid TOTP code")
    u.totp_enabled = False
    u.totp_secret = None
    db.commit()
    return {"message": "2FA disabled"}

# - OAuth -

@router.get("/oauth/google/url")
def google_url():
    from app.core.config import GOOGLE_CLIENT_ID as GID, FRONTEND_URL as FU
    if not GID: raise HTTPException(400, "Google OAuth not configured")
    state = secrets.token_urlsafe(16)
    redirect = f"{FU}/oauth/callback"
    url = (f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GID}"
           f"&redirect_uri={redirect}&response_type=code&scope=openid%20email%20profile"
           f"&state={state}&access_type=offline")
    return {"url": url, "state": state}

@router.get("/oauth/github/url")
def github_url():
    from app.core.config import GITHUB_CLIENT_ID as GID, FRONTEND_URL as FU
    if not GID: raise HTTPException(400, "GitHub OAuth not configured")
    state = secrets.token_urlsafe(16)
    redirect = f"{FU}/oauth/callback"
    url = (f"https://github.com/login/oauth/authorize?client_id={GID}"
           f"&redirect_uri={redirect}&scope=user:email&state={state}")
    return {"url": url, "state": state}

@router.post("/oauth/google/callback", response_model=TokenResponse)
async def google_callback(body: OAuthCallback, db: Session = Depends(get_db)):
    from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, FRONTEND_URL
    redirect = f"{FRONTEND_URL}/oauth/callback"
    async with httpx.AsyncClient() as c:
        tr = await c.post("https://oauth2.googleapis.com/token", data={
            "code": body.code, "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET, "redirect_uri": redirect,
            "grant_type": "authorization_code"})
        if tr.status_code != 200: raise HTTPException(400, f"Google error: {tr.text}")
        ur = await c.get("https://www.googleapis.com/oauth2/v2/userinfo",
                         headers={"Authorization": f"Bearer {tr.json()['access_token']}"})
        email = ur.json().get("email")
    if not email: raise HTTPException(400, "No email from Google")
    user = get_or_create_oauth_user(db, email)
    
    # Create token with user_id, email, tier, role (Requirement 17.2)
    from app.utils.auth import create_user_token
    access_token = create_user_token(
        user_id=user.id,
        email=user.email,
        tier=user.tier,
        role=user.role
    )
    
    try:
        from app.services.email_service import notify_oauth_login
        notify_oauth_login(email, "google")
    except Exception:
        pass
    
    return TokenResponse(access_token=access_token)

@router.post("/oauth/github/callback", response_model=TokenResponse)
async def github_callback(body: OAuthCallback, db: Session = Depends(get_db)):
    from app.core.config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, FRONTEND_URL
    redirect = f"{FRONTEND_URL}/oauth/callback"
    async with httpx.AsyncClient() as c:
        tr = await c.post("https://github.com/login/oauth/access_token", data={
            "client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET,
            "code": body.code, "redirect_uri": redirect},
            headers={"Accept": "application/json"})
        token = tr.json().get("access_token")
        ur = await c.get("https://api.github.com/user",
                         headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        email = ur.json().get("email")
        if not email:
            er = await c.get("https://api.github.com/user/emails",
                             headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
            emails = er.json()
            email = next((e["email"] for e in emails if e.get("primary") and e.get("verified")), None)
    if not email: raise HTTPException(400, "No email from GitHub")
    user = get_or_create_oauth_user(db, email)
    
    # Create token with user_id, email, tier, role (Requirement 17.2)
    from app.utils.auth import create_user_token
    access_token = create_user_token(
        user_id=user.id,
        email=user.email,
        tier=user.tier,
        role=user.role
    )
    
    try:
        from app.services.email_service import notify_oauth_login
        notify_oauth_login(email, "github")
    except Exception:
        pass
    
    return TokenResponse(access_token=access_token)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password")
def change_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    u = authenticate(db, user["sub"], data.old_password)
    if not u:
        raise HTTPException(401, "Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(422, "New password must be at least 6 characters")
    u.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed"}

# - Forgot / Reset Password -

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generate a reset token and email it. Always returns 200 to avoid user enumeration."""
    user = get_user(db, data.email)
    if user:
        token = secrets.token_urlsafe(32)
        _reset_tokens[token] = {
            "email": data.email,
            "expires": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        try:
            from app.core.config import FRONTEND_URL
            from app.services.email_service import send_password_reset_email
            send_password_reset_email(data.email, token, FRONTEND_URL)
        except Exception:
            pass
    return {"message": "If that email exists, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Validate reset token and update password."""
    entry = _reset_tokens.get(data.token)
    if not entry:
        raise HTTPException(400, "Invalid or expired reset token")
    if datetime.now(timezone.utc) > entry["expires"]:
        del _reset_tokens[data.token]
        raise HTTPException(400, "Reset token has expired")
    if len(data.new_password) < 6:
        raise HTTPException(422, "Password must be at least 6 characters")
    user = get_user(db, entry["email"])
    if not user:
        raise HTTPException(404, "User not found")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    del _reset_tokens[data.token]
    return {"message": "Password has been reset successfully"}
