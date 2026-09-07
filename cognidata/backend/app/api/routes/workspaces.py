"""Workspace routes - CRUD + invitations with email."""
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.workspace import Workspace, WorkspaceMember, Invitation
from app.models.user import User

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class WorkspaceCreate(BaseModel):
    name: str
    description: str = ""


class InviteRequest(BaseModel):
    email: str
    role: str = "viewer"


class JoinRequest(BaseModel):
    token: str


# - List workspaces -

@router.get("")
def list_workspaces(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == user["email"]).first()
    if not u:
        return []
    owned = db.query(Workspace).filter(Workspace.owner_id == u.id).all()
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == u.id).all()
    member_ws_ids = {m.workspace_id for m in memberships}
    member_ws = db.query(Workspace).filter(Workspace.id.in_(member_ws_ids)).all()
    all_ws = {w.id: w for w in owned + member_ws}
    result = []
    for w in all_ws.values():
        owner = db.query(User).filter(User.id == w.owner_id).first()
        members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == w.id).all()
        result.append({
            "id": w.id, "name": w.name, "description": w.description,
            "owner": owner.email if owner else "", "created_at": w.created_at,
            "is_owner": w.owner_id == u.id,
            "member_count": len(members),
            "role": "owner" if w.owner_id == u.id else next(
                (m.role for m in memberships if m.workspace_id == w.id), "viewer"),
        })
    return result


# - Create workspace -

@router.post("", status_code=201)
def create_workspace(data: WorkspaceCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == user["email"]).first()
    if not u:
        raise HTTPException(404, "User not found")
    ws = Workspace(name=data.name, description=data.description, owner_id=u.id,
                   created_at=datetime.now(timezone.utc).isoformat())
    db.add(ws); db.commit(); db.refresh(ws)
    return {"id": ws.id, "name": ws.name, "message": "Workspace created"}


# - Delete workspace -

@router.delete("/{ws_id}", status_code=204)
def delete_workspace(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == user["email"]).first()
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if ws.owner_id != u.id:
        raise HTTPException(403, "Only owner can delete")
    db.delete(ws); db.commit()


# - Members -

@router.get("/{ws_id}/members")
def list_members(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws_id).all()
    result = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        result.append({"user_id": m.user_id, "email": u.email if u else "", "role": m.role})
    return result


@router.delete("/{ws_id}/members/{user_id}", status_code=204)
def remove_member(ws_id: int, user_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == user["email"]).first()
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if ws.owner_id != u.id:
        raise HTTPException(403, "Only owner can remove members")
    m = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == ws_id,
        WorkspaceMember.user_id == user_id).first()
    if m:
        db.delete(m); db.commit()


# - Invitations -

@router.post("/{ws_id}/invite")
def invite(ws_id: int, data: InviteRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    # Check if already a member
    invitee = db.query(User).filter(User.email == data.email).first()
    if invitee:
        existing = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == ws_id,
            WorkspaceMember.user_id == invitee.id).first()
        if existing:
            raise HTTPException(400, f"{data.email} is already a member of this workspace")

    token = str(uuid.uuid4())
    expires = (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()
    inv = Invitation(token=token, workspace_id=ws_id, email=data.email, role=data.role,
                     status="pending", expires_at=expires,
                     created_at=datetime.now(timezone.utc).isoformat())
    db.add(inv); db.commit()

    # Send invitation email directly (not via stale config)
    try:
        import pathlib
        env_path = pathlib.Path(__file__).resolve().parents[3] / ".env"
        env = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
        frontend_url = env.get("FRONTEND_URL", "http://localhost:5173")
        from app.services.email_service import send_invitation_email
        send_invitation_email(data.email, ws.name, data.role, token, frontend_url)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Invitation email failed: %s", e)

    return {"message": f"Invitation sent to {data.email}", "token": token}


@router.get("/{ws_id}/invitations")
def list_invitations(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    invs = db.query(Invitation).filter(Invitation.workspace_id == ws_id).all()
    now = datetime.now(timezone.utc).isoformat()
    result = []
    for inv in invs:
        status = inv.status
        if status == "pending" and inv.expires_at < now:
            status = "expired"
        result.append({"id": inv.id, "email": inv.email, "role": inv.role,
                        "status": status, "expires_at": inv.expires_at,
                        "token": inv.token})
    return result


@router.post("/{ws_id}/invitations/{inv_id}/resend")
def resend_invitation(ws_id: int, inv_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    inv = db.query(Invitation).filter(Invitation.id == inv_id, Invitation.workspace_id == ws_id).first()
    if not inv:
        raise HTTPException(404, "Invitation not found")
    inv.expires_at = (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()
    inv.status = "pending"
    db.commit()
    try:
        import pathlib
        env_path = pathlib.Path(__file__).resolve().parents[3] / ".env"
        env = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
        frontend_url = env.get("FRONTEND_URL", "http://localhost:5173")
        from app.services.email_service import send_invitation_email
        send_invitation_email(inv.email, ws.name, inv.role, inv.token, frontend_url)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Resend email failed: %s", e)
    return {"message": f"Invitation resent to {inv.email}"}


@router.delete("/{ws_id}/invitations/{inv_id}", status_code=204)
def revoke_invitation(ws_id: int, inv_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    inv = db.query(Invitation).filter(Invitation.id == inv_id, Invitation.workspace_id == ws_id).first()
    if not inv:
        raise HTTPException(404, "Invitation not found")
    db.delete(inv); db.commit()


# - Join via token -

@router.get("/join/info")
def get_join_info(token: str, db: Session = Depends(get_db)):
    """Get workspace info for an invitation token (no auth required)."""
    inv = db.query(Invitation).filter(Invitation.token == token).first()
    if not inv:
        raise HTTPException(400, "Invalid invitation token")
    now = datetime.now(timezone.utc).isoformat()
    if inv.expires_at < now:
        raise HTTPException(400, "Invitation has expired")
    if inv.status != "pending":
        raise HTTPException(400, "Invitation already used")
    ws = db.query(Workspace).filter(Workspace.id == inv.workspace_id).first()
    return {"workspace_name": ws.name if ws else "", "role": inv.role, "email": inv.email}


@router.post("/join")
def join_workspace(data: JoinRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    inv = db.query(Invitation).filter(Invitation.token == data.token).first()
    if not inv:
        raise HTTPException(400, "Invalid invitation token")
    now = datetime.now(timezone.utc).isoformat()
    if inv.expires_at < now:
        raise HTTPException(400, "Invitation has expired")
    if inv.status != "pending":
        raise HTTPException(400, "Invitation already used")
    u = db.query(User).filter(User.email == user["email"]).first()
    if not u:
        raise HTTPException(404, "User not found")
    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == inv.workspace_id,
        WorkspaceMember.user_id == u.id).first()
    if not existing:
        m = WorkspaceMember(workspace_id=inv.workspace_id, user_id=u.id, role=inv.role)
        db.add(m)
    inv.status = "accepted"
    db.commit()
    ws = db.query(Workspace).filter(Workspace.id == inv.workspace_id).first()
    try:
        from app.services.email_service import notify_workspace_joined
        owner = db.query(User).filter(User.id == ws.owner_id).first() if ws else None
        if owner and owner.email != u.email:
            notify_workspace_joined(owner.email, u.email, ws.name if ws else "", inv.role)
    except Exception:
        pass
    return {"message": f"Joined workspace '{ws.name if ws else ''}' as {inv.role}"}


# - Advanced Workspace Features -

# In-memory stores for features not requiring DB schema changes
import json as _json
from collections import defaultdict as _dd

_activity: dict = _dd(list)       # ws_id -> [{event, user, ts, detail}]
_pinned: dict = _dd(list)         # ws_id -> [{id, title, chart_config, pinned_by, ts}]
_ws_settings: dict = {}           # ws_id -> {max_members, allow_guest_view, tags}
_shared_datasets: dict = _dd(dict) # ws_id -> {name: {uploader, rows, cols, ts}}


def _log_activity(ws_id: int, email: str, event: str, detail: str = ""):
    _activity[ws_id].append({
        "event": event, "user": email,
        "ts": datetime.now(timezone.utc).isoformat(),
        "detail": detail,
    })
    # Keep last 200 events
    if len(_activity[ws_id]) > 200:
        _activity[ws_id] = _activity[ws_id][-200:]


def _get_member_role(ws_id: int, user_email: str, db: Session) -> str:
    u = db.query(User).filter(User.email == user_email).first()
    if not u:
        return ""
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if ws and ws.owner_id == u.id:
        return "owner"
    m = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == ws_id,
        WorkspaceMember.user_id == u.id).first()
    return m.role if m else ""


# - 1. Get workspace detail -

@router.get("/{ws_id}")
def get_workspace(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    owner = db.query(User).filter(User.id == ws.owner_id).first()
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws_id).all()
    settings = _ws_settings.get(ws_id, {"max_members": 50, "allow_guest_view": False, "tags": []})
    return {
        "id": ws.id, "name": ws.name, "description": ws.description,
        "owner": owner.email if owner else "", "created_at": ws.created_at,
        "member_count": len(members) + 1,
        "role": role,
        "settings": settings,
        "pinned_count": len(_pinned.get(ws_id, [])),
        "shared_datasets": len(_shared_datasets.get(ws_id, {})),
    }


# - 2. Update workspace settings -

class WorkspaceUpdate(BaseModel):
    name: str = ""
    description: str = ""
    max_members: int = 50
    allow_guest_view: bool = False
    tags: list = []


@router.patch("/{ws_id}")
def update_workspace(ws_id: int, data: WorkspaceUpdate,
                     user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == user["email"]).first()
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if ws.owner_id != u.id:
        raise HTTPException(403, "Only owner can update workspace")
    if data.name:
        ws.name = data.name
    if data.description is not None:
        ws.description = data.description
    db.commit()
    _ws_settings[ws_id] = {
        "max_members": data.max_members,
        "allow_guest_view": data.allow_guest_view,
        "tags": data.tags,
    }
    _log_activity(ws_id, user["email"], "workspace_updated", f"Settings updated by {user['email']}")
    return {"message": "Workspace updated"}


# - 3. Change member role -

class RoleUpdate(BaseModel):
    role: str  # viewer | editor | admin


@router.patch("/{ws_id}/members/{user_id}/role")
def update_member_role(ws_id: int, user_id: int, data: RoleUpdate,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == user["email"]).first()
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    # Owner or admin can change roles
    my_role = _get_member_role(ws_id, user["email"], db)
    if my_role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can change roles")
    if data.role not in ("viewer", "editor", "admin"):
        raise HTTPException(400, "Role must be viewer, editor, or admin")
    m = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == ws_id,
        WorkspaceMember.user_id == user_id).first()
    if not m:
        raise HTTPException(404, "Member not found")
    target = db.query(User).filter(User.id == user_id).first()
    old_role = m.role
    m.role = data.role
    db.commit()
    _log_activity(ws_id, user["email"], "role_changed",
                  f"{target.email if target else user_id} changed from {old_role} to {data.role}")
    return {"message": f"Role updated to {data.role}"}


# - 4. Activity feed -

@router.get("/{ws_id}/activity")
def get_activity(ws_id: int, limit: int = 50,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    events = list(reversed(_activity.get(ws_id, [])))[:limit]
    return {"events": events, "total": len(_activity.get(ws_id, []))}


# - 5. Shared datasets -

@router.post("/{ws_id}/datasets/share")
def share_dataset(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Share the user's active dataset with the workspace."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    if role == "viewer":
        raise HTTPException(403, "Viewers cannot share datasets")
    from app.services.data_store import get as get_df
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset uploaded")
    name = f"{user['email'].split('@')[0]}_{datetime.now(timezone.utc).strftime('%m%d_%H%M')}"
    _shared_datasets[ws_id][name] = {
        "name": name, "uploader": user["email"],
        "rows": len(df), "cols": len(df.columns),
        "columns": list(df.columns),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _log_activity(ws_id, user["email"], "dataset_shared",
                  f"Shared dataset '{name}' ({len(df)} rows, {len(df.columns)} cols)")
    return {"message": f"Dataset shared as '{name}'", "name": name}


@router.get("/{ws_id}/datasets")
def list_shared_datasets(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"datasets": list(_shared_datasets.get(ws_id, {}).values())}


@router.post("/{ws_id}/datasets/{name}/load")
def load_shared_dataset(ws_id: int, name: str,
                        user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Load a workspace shared dataset as the user's active dataset."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    ds = _shared_datasets.get(ws_id, {}).get(name)
    if not ds:
        raise HTTPException(404, "Shared dataset not found")
    # Find the uploader's dataset and copy it to this user
    from app.services.data_store import get as get_df, save as save_df
    uploader_df = get_df(ds["uploader"])
    if uploader_df is None:
        raise HTTPException(404, "Original dataset no longer available")
    save_df(user["email"], uploader_df, name)
    _log_activity(ws_id, user["email"], "dataset_loaded",
                  f"Loaded shared dataset '{name}' from {ds['uploader']}")
    return {"message": f"Dataset '{name}' loaded as your active dataset"}


# - 6. Pinned dashboards -

class PinRequest(BaseModel):
    title: str
    chart_type: str
    x_col: str = ""
    y_col: str = ""
    description: str = ""


@router.post("/{ws_id}/pins")
def pin_chart(ws_id: int, data: PinRequest,
              user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    if role == "viewer":
        raise HTTPException(403, "Viewers cannot pin charts")
    pin_id = str(uuid.uuid4())[:8]
    pin = {
        "id": pin_id, "title": data.title,
        "chart_type": data.chart_type, "x_col": data.x_col, "y_col": data.y_col,
        "description": data.description,
        "pinned_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _pinned[ws_id].append(pin)
    _log_activity(ws_id, user["email"], "chart_pinned", f"Pinned chart '{data.title}'")
    return {"message": "Chart pinned", "pin": pin}


@router.get("/{ws_id}/pins")
def list_pins(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"pins": _pinned.get(ws_id, [])}


@router.delete("/{ws_id}/pins/{pin_id}", status_code=204)
def delete_pin(ws_id: int, pin_id: str,
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    pins = _pinned.get(ws_id, [])
    pin = next((p for p in pins if p["id"] == pin_id), None)
    if not pin:
        raise HTTPException(404, "Pin not found")
    if pin["pinned_by"] != user["email"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Can only delete your own pins")
    _pinned[ws_id] = [p for p in pins if p["id"] != pin_id]
    _log_activity(ws_id, user["email"], "chart_unpinned", f"Removed pin '{pin['title']}'")


# - 7. Workspace analytics -

@router.get("/{ws_id}/analytics")
def workspace_analytics(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws_id).all()
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    events = _activity.get(ws_id, [])
    # Count events by type
    event_counts: dict = {}
    for e in events:
        event_counts[e["event"]] = event_counts.get(e["event"], 0) + 1
    # Active members (had activity in last 7 days)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    active_users = {e["user"] for e in events if e["ts"] > cutoff}
    # Role distribution
    role_dist: dict = {"owner": 1, "admin": 0, "editor": 0, "viewer": 0}
    for m in members:
        role_dist[m.role] = role_dist.get(m.role, 0) + 1
    return {
        "workspace_id": ws_id,
        "workspace_name": ws.name if ws else "",
        "total_members": len(members) + 1,
        "active_members_7d": len(active_users),
        "total_events": len(events),
        "event_breakdown": event_counts,
        "role_distribution": role_dist,
        "shared_datasets": len(_shared_datasets.get(ws_id, {})),
        "pinned_charts": len(_pinned.get(ws_id, [])),
        "recent_activity": list(reversed(events))[:5],
    }


# - 8. Transfer ownership -

class TransferRequest(BaseModel):
    new_owner_email: str


@router.post("/{ws_id}/transfer-ownership")
def transfer_ownership(ws_id: int, data: TransferRequest,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == user["email"]).first()
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if ws.owner_id != u.id:
        raise HTTPException(403, "Only owner can transfer ownership")
    new_owner = db.query(User).filter(User.email == data.new_owner_email).first()
    if not new_owner:
        raise HTTPException(404, "New owner not found - they must be a registered user")
    # Ensure new owner is a member
    m = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == ws_id,
        WorkspaceMember.user_id == new_owner.id).first()
    if not m:
        raise HTTPException(400, "New owner must be a current member")
    old_owner_email = u.email
    ws.owner_id = new_owner.id
    m.role = "admin"  # previous owner becomes admin
    # Add old owner as admin member
    old_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == ws_id,
        WorkspaceMember.user_id == u.id).first()
    if not old_member:
        db.add(WorkspaceMember(workspace_id=ws_id, user_id=u.id, role="admin"))
    db.commit()
    _log_activity(ws_id, user["email"], "ownership_transferred",
                  f"Ownership transferred from {old_owner_email} to {data.new_owner_email}")
    return {"message": f"Ownership transferred to {data.new_owner_email}"}


# - Advanced Workspace Features Batch 2 -

_chat: dict = _dd(list)           # ws_id -> [{id, user, msg, ts, edited}]
_saved_queries: dict = _dd(list)  # ws_id -> [{id, title, query, type, user, ts, runs}]
_announcements: dict = _dd(list)  # ws_id -> [{id, title, body, user, ts, pinned}]
_last_seen: dict = {}             # user_email -> ts
_ws_reports: dict = _dd(list)    # ws_id -> [{id, name, frequency, type, created_by, ts}]
_ws_templates = [
    {"id":"data_team",    "name":"Data Team",       "description":"Editor roles, shared datasets enabled", "max_members":20, "tags":["data","analytics"]},
    {"id":"exec_review",  "name":"Exec Review",     "description":"Viewer-only, pinned KPI dashboards",    "max_members":10, "tags":["executive","kpi"]},
    {"id":"ml_project",   "name":"ML Project",      "description":"Full access, ML model sharing",         "max_members":15, "tags":["ml","ai"]},
    {"id":"open_collab",  "name":"Open Collaboration","description":"Public join, all roles allowed",       "max_members":50, "tags":["open","community"]},
]
_next_chat_id = 1
_next_query_id = 1
_next_ann_id = 1
_next_report_id = 1


# - 9. Workspace Chat -

class ChatMessage(BaseModel):
    message: str


class ChatEdit(BaseModel):
    message: str


@router.get("/{ws_id}/chat")
def get_chat(ws_id: int, limit: int = 100,
             user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _last_seen[user["email"]] = datetime.now(timezone.utc).isoformat()
    msgs = list(reversed(_chat.get(ws_id, [])))[:limit]
    return {"messages": list(reversed(msgs)), "total": len(_chat.get(ws_id, []))}


@router.post("/{ws_id}/chat")
def send_chat(ws_id: int, data: ChatMessage,
              user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_chat_id
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    if not data.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    msg = {
        "id": _next_chat_id, "user": user["email"],
        "message": data.message.strip(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "edited": False,
    }
    _next_chat_id += 1
    _chat[ws_id].append(msg)
    if len(_chat[ws_id]) > 500:
        _chat[ws_id] = _chat[ws_id][-500:]
    _last_seen[user["email"]] = msg["ts"]
    _log_activity(ws_id, user["email"], "chat_message", data.message[:60])
    return msg


@router.patch("/{ws_id}/chat/{msg_id}")
def edit_chat(ws_id: int, msg_id: int, data: ChatEdit,
              user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    msgs = _chat.get(ws_id, [])
    msg = next((m for m in msgs if m["id"] == msg_id), None)
    if not msg:
        raise HTTPException(404, "Message not found")
    if msg["user"] != user["email"]:
        raise HTTPException(403, "Can only edit your own messages")
    msg["message"] = data.message.strip()
    msg["edited"] = True
    return msg


@router.delete("/{ws_id}/chat/{msg_id}", status_code=204)
def delete_chat(ws_id: int, msg_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    msgs = _chat.get(ws_id, [])
    msg = next((m for m in msgs if m["id"] == msg_id), None)
    if not msg:
        raise HTTPException(404, "Message not found")
    if msg["user"] != user["email"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others' messages")
    _chat[ws_id] = [m for m in msgs if m["id"] != msg_id]


# - 10. Saved Queries -

class SavedQuery(BaseModel):
    title: str
    query: str
    query_type: str = "natural_language"  # natural_language | sql | python


@router.get("/{ws_id}/queries")
def list_queries(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"queries": _saved_queries.get(ws_id, [])}


@router.post("/{ws_id}/queries")
def save_query(ws_id: int, data: SavedQuery,
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_query_id
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    if role == "viewer":
        raise HTTPException(403, "Viewers cannot save queries")
    q = {
        "id": _next_query_id, "title": data.title,
        "query": data.query, "query_type": data.query_type,
        "created_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "runs": 0,
    }
    _next_query_id += 1
    _saved_queries[ws_id].append(q)
    _log_activity(ws_id, user["email"], "query_saved", f"Saved query '{data.title}'")
    return q


@router.post("/{ws_id}/queries/{query_id}/run")
def run_saved_query(ws_id: int, query_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a query as run and return it for execution."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    q = next((q for q in _saved_queries.get(ws_id, []) if q["id"] == query_id), None)
    if not q:
        raise HTTPException(404, "Query not found")
    q["runs"] = q.get("runs", 0) + 1
    q["last_run_by"] = user["email"]
    q["last_run_ts"] = datetime.now(timezone.utc).isoformat()
    _log_activity(ws_id, user["email"], "query_run", f"Ran query '{q['title']}'")
    return {"query": q, "message": "Query ready to execute"}


@router.delete("/{ws_id}/queries/{query_id}", status_code=204)
def delete_query(ws_id: int, query_id: int,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    queries = _saved_queries.get(ws_id, [])
    q = next((q for q in queries if q["id"] == query_id), None)
    if not q:
        raise HTTPException(404, "Query not found")
    if q["created_by"] != user["email"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others' queries")
    _saved_queries[ws_id] = [q for q in queries if q["id"] != query_id]


# - 11. Announcements -

class AnnouncementCreate(BaseModel):
    title: str
    body: str
    pinned: bool = False


@router.get("/{ws_id}/announcements")
def list_announcements(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _last_seen[user["email"]] = datetime.now(timezone.utc).isoformat()
    return {"announcements": list(reversed(_announcements.get(ws_id, [])))}


@router.post("/{ws_id}/announcements")
def create_announcement(ws_id: int, data: AnnouncementCreate,
                        user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_ann_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can post announcements")
    ann = {
        "id": _next_ann_id, "title": data.title, "body": data.body,
        "pinned": data.pinned, "created_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_ann_id += 1
    _announcements[ws_id].append(ann)
    _log_activity(ws_id, user["email"], "announcement_posted", f"'{data.title}'")
    return ann


@router.delete("/{ws_id}/announcements/{ann_id}", status_code=204)
def delete_announcement(ws_id: int, ann_id: int,
                        user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete announcements")
    _announcements[ws_id] = [a for a in _announcements.get(ws_id, []) if a["id"] != ann_id]


# - 12. Member Online Status -

@router.get("/{ws_id}/presence")
def get_presence(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _last_seen[user["email"]] = datetime.now(timezone.utc).isoformat()
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws_id).all()
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    all_emails = set()
    if ws:
        owner = db.query(User).filter(User.id == ws.owner_id).first()
        if owner:
            all_emails.add(owner.email)
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            all_emails.add(u.email)
    now = datetime.now(timezone.utc)
    cutoff_online = (now - timedelta(minutes=5)).isoformat()
    cutoff_away   = (now - timedelta(minutes=30)).isoformat()
    result = []
    for email in all_emails:
        last = _last_seen.get(email)
        if last and last > cutoff_online:
            status = "online"
        elif last and last > cutoff_away:
            status = "away"
        else:
            status = "offline"
        result.append({"email": email, "status": status, "last_seen": last})
    return {"presence": result}


@router.post("/{ws_id}/presence/ping")
def ping_presence(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Heartbeat - call every 60s to stay 'online'."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _last_seen[user["email"]] = datetime.now(timezone.utc).isoformat()
    return {"status": "ok", "ts": _last_seen[user["email"]]}


# - 13. Workspace Scheduled Reports -

class WsReportCreate(BaseModel):
    name: str
    frequency: str = "Weekly"   # Daily | Weekly | Monthly
    report_type: str = "pdf"    # pdf | csv | excel
    recipients: list = []       # list of member emails


@router.get("/{ws_id}/reports")
def list_ws_reports(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"reports": _ws_reports.get(ws_id, [])}


@router.post("/{ws_id}/reports")
def create_ws_report(ws_id: int, data: WsReportCreate,
                     user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_report_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create reports")
    rpt = {
        "id": _next_report_id, "name": data.name,
        "frequency": data.frequency, "report_type": data.report_type,
        "recipients": data.recipients, "created_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "active": True, "last_run": None,
    }
    _next_report_id += 1
    _ws_reports[ws_id].append(rpt)
    _log_activity(ws_id, user["email"], "report_scheduled", f"'{data.name}' ({data.frequency})")
    return rpt


@router.delete("/{ws_id}/reports/{report_id}", status_code=204)
def delete_ws_report(ws_id: int, report_id: int,
                     user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _ws_reports[ws_id] = [r for r in _ws_reports.get(ws_id, []) if r["id"] != report_id]


# - 14. Audit Log Export -

from fastapi.responses import StreamingResponse
import csv, io as _io


@router.get("/{ws_id}/audit-export")
def export_audit_log(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can export audit log")
    events = _activity.get(ws_id, [])
    buf = _io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["ts", "user", "event", "detail"])
    writer.writeheader()
    for e in events:
        writer.writerow({"ts": e.get("ts",""), "user": e.get("user",""),
                         "event": e.get("event",""), "detail": e.get("detail","")})
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=workspace_{ws_id}_audit.csv"},
    )


# - 15. Workspace Templates -

@router.get("/templates")
def list_templates():
    """List available workspace templates."""
    return {"templates": _ws_templates}


class TemplateCreate(BaseModel):
    template_id: str
    name: str
    description: str = ""


@router.post("/from-template", status_code=201)
def create_from_template(data: TemplateCreate,
                         user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a workspace pre-configured from a template."""
    tmpl = next((t for t in _ws_templates if t["id"] == data.template_id), None)
    if not tmpl:
        raise HTTPException(404, "Template not found")
    u = db.query(User).filter(User.email == user["email"]).first()
    if not u:
        raise HTTPException(404, "User not found")
    ws = Workspace(
        name=data.name or tmpl["name"],
        description=data.description or tmpl["description"],
        owner_id=u.id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(ws); db.commit(); db.refresh(ws)
    _ws_settings[ws.id] = {
        "max_members": tmpl["max_members"],
        "allow_guest_view": False,
        "tags": tmpl["tags"],
        "template": tmpl["id"],
    }
    _log_activity(ws.id, user["email"], "workspace_created", f"From template '{tmpl['name']}'")
    return {"id": ws.id, "name": ws.name, "template": tmpl["id"], "message": "Workspace created from template"}


# - 16. Workspace Search -

@router.get("/search")
def search_workspaces(q: str = "", tag: str = "",
                      user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Search workspaces by name or tag."""
    u = db.query(User).filter(User.email == user["email"]).first()
    if not u:
        return []
    owned = db.query(Workspace).filter(Workspace.owner_id == u.id).all()
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == u.id).all()
    member_ws_ids = {m.workspace_id for m in memberships}
    member_ws = db.query(Workspace).filter(Workspace.id.in_(member_ws_ids)).all()
    all_ws = {w.id: w for w in owned + member_ws}
    results = []
    for w in all_ws.values():
        settings = _ws_settings.get(w.id, {})
        tags = settings.get("tags", [])
        name_match = q.lower() in w.name.lower() if q else True
        tag_match = tag.lower() in [t.lower() for t in tags] if tag else True
        if name_match and tag_match:
            results.append({
                "id": w.id, "name": w.name, "description": w.description,
                "tags": tags, "is_owner": w.owner_id == u.id,
            })
    return results


# - Advanced Workspace Features Batch 3 -

_notebooks: dict = _dd(list)    # ws_id -> [{id, title, content, author, ts, updated}]
_tasks: dict = _dd(list)        # ws_id -> [{id, title, desc, status, assignee, priority, due, created_by, ts}]
_ws_alerts: dict = _dd(list)    # ws_id -> [{id, metric, threshold, condition, active, created_by}]
_insights: dict = _dd(list)     # ws_id -> [{id, text, ts, source}]
_webhooks: dict = _dd(list)     # ws_id -> [{id, url, events, active, created_by}]
_versions: dict = _dd(list)     # ws_id -> [{id, name, dataset_name, rows, cols, ts, saved_by, tag}]
_goals: dict = _dd(list)        # ws_id -> [{id, title, metric, target, current, unit, deadline, created_by}]
_contributions: dict = _dd(lambda: _dd(int))  # ws_id -> {email -> count}

_next_nb_id = 1
_next_task_id = 1
_next_ws_alert_id = 1
_next_webhook_id = 1
_next_version_id = 1
_next_goal_id = 1


def _track(ws_id, email, action):
    _contributions[ws_id][email] += 1
    _log_activity(ws_id, email, action)


# - 17. Workspace Notebooks -

class NotebookCreate(BaseModel):
    title: str
    content: str = ""


class NotebookUpdate(BaseModel):
    title: str = ""
    content: str = ""


@router.get("/{ws_id}/notebooks")
def list_notebooks(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"notebooks": list(reversed(_notebooks.get(ws_id, [])))}


@router.post("/{ws_id}/notebooks")
def create_notebook(ws_id: int, data: NotebookCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_nb_id
    role = _get_member_role(ws_id, user["email"], db)
    if not role or role == "viewer":
        raise HTTPException(403, "Viewers cannot create notebooks")
    nb = {
        "id": _next_nb_id, "title": data.title, "content": data.content,
        "author": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(), "updated_by": user["email"],
    }
    _next_nb_id += 1
    _notebooks[ws_id].append(nb)
    _track(ws_id, user["email"], "notebook_created")
    return nb


@router.patch("/{ws_id}/notebooks/{nb_id}")
def update_notebook(ws_id: int, nb_id: int, data: NotebookUpdate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role or role == "viewer":
        raise HTTPException(403, "Viewers cannot edit notebooks")
    nb = next((n for n in _notebooks.get(ws_id, []) if n["id"] == nb_id), None)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    if data.title:
        nb["title"] = data.title
    if data.content is not None:
        nb["content"] = data.content
    nb["updated"] = datetime.now(timezone.utc).isoformat()
    nb["updated_by"] = user["email"]
    _track(ws_id, user["email"], "notebook_updated")
    return nb


@router.delete("/{ws_id}/notebooks/{nb_id}", status_code=204)
def delete_notebook(ws_id: int, nb_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    nbs = _notebooks.get(ws_id, [])
    nb = next((n for n in nbs if n["id"] == nb_id), None)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    if nb["author"] != user["email"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others notebooks")
    _notebooks[ws_id] = [n for n in nbs if n["id"] != nb_id]


# - 18. Task Board (Kanban) -

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee: str = ""
    priority: str = "medium"   # low | medium | high | critical
    due: str = ""
    status: str = "todo"       # todo | in_progress | review | done


class TaskUpdate(BaseModel):
    title: str = ""
    description: str = ""
    assignee: str = ""
    priority: str = ""
    due: str = ""
    status: str = ""


@router.get("/{ws_id}/tasks")
def list_tasks(ws_id: int, status: str = "", assignee: str = "",
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    tasks = _tasks.get(ws_id, [])
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if assignee:
        tasks = [t for t in tasks if t["assignee"] == assignee]
    # Group by status for kanban view
    board = {"todo": [], "in_progress": [], "review": [], "done": []}
    for t in tasks:
        board.setdefault(t["status"], []).append(t)
    return {"tasks": tasks, "board": board, "total": len(tasks)}


@router.post("/{ws_id}/tasks")
def create_task(ws_id: int, data: TaskCreate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_task_id
    role = _get_member_role(ws_id, user["email"], db)
    if not role or role == "viewer":
        raise HTTPException(403, "Viewers cannot create tasks")
    task = {
        "id": _next_task_id, "title": data.title, "description": data.description,
        "assignee": data.assignee, "priority": data.priority,
        "due": data.due, "status": data.status,
        "created_by": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_task_id += 1
    _tasks[ws_id].append(task)
    _track(ws_id, user["email"], "task_created")
    return task


@router.patch("/{ws_id}/tasks/{task_id}")
def update_task(ws_id: int, task_id: int, data: TaskUpdate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    task = next((t for t in _tasks.get(ws_id, []) if t["id"] == task_id), None)
    if not task:
        raise HTTPException(404, "Task not found")
    for field in ("title", "description", "assignee", "priority", "due", "status"):
        val = getattr(data, field)
        if val:
            task[field] = val
    task["updated_by"] = user["email"]
    task["updated_ts"] = datetime.now(timezone.utc).isoformat()
    _track(ws_id, user["email"], "task_updated")
    return task


@router.delete("/{ws_id}/tasks/{task_id}", status_code=204)
def delete_task(ws_id: int, task_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _tasks[ws_id] = [t for t in _tasks.get(ws_id, []) if t["id"] != task_id]


# - 19. Workspace Data Alerts -

class WsAlertCreate(BaseModel):
    metric: str
    threshold: float
    condition: str = "above"   # above | below | equals
    notify_all: bool = True


@router.get("/{ws_id}/data-alerts")
def list_ws_alerts(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"alerts": _ws_alerts.get(ws_id, [])}


@router.post("/{ws_id}/data-alerts")
def create_ws_alert(ws_id: int, data: WsAlertCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_ws_alert_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create alerts")
    alert = {
        "id": _next_ws_alert_id, "metric": data.metric,
        "threshold": data.threshold, "condition": data.condition,
        "notify_all": data.notify_all, "active": True,
        "created_by": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
        "triggered_count": 0,
    }
    _next_ws_alert_id += 1
    _ws_alerts[ws_id].append(alert)
    _log_activity(ws_id, user["email"], "alert_created", f"{data.metric} {data.condition} {data.threshold}")
    return alert


@router.post("/{ws_id}/data-alerts/check")
def check_ws_alerts(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check current dataset against workspace alerts."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    from app.services.data_store import get as get_df
    df = get_df(user["email"])
    if df is None:
        return {"triggered": [], "checked": 0}
    alerts = _ws_alerts.get(ws_id, [])
    triggered = []
    for alert in alerts:
        if not alert["active"]:
            continue
        col = alert["metric"]
        if col not in df.columns:
            continue
        import numpy as np
        val = float(df[col].mean())
        thr = alert["threshold"]
        cond = alert["condition"]
        hit = (cond == "above" and val > thr) or (cond == "below" and val < thr) or (cond == "equals" and abs(val - thr) < 0.01)
        if hit:
            alert["triggered_count"] = alert.get("triggered_count", 0) + 1
            triggered.append({"alert": alert, "current_value": round(val, 3)})
            _log_activity(ws_id, user["email"], "alert_triggered", f"{col}={val:.2f} {cond} {thr}")
    return {"triggered": triggered, "checked": len(alerts)}


@router.delete("/{ws_id}/data-alerts/{alert_id}", status_code=204)
def delete_ws_alert(ws_id: int, alert_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _ws_alerts[ws_id] = [a for a in _ws_alerts.get(ws_id, []) if a["id"] != alert_id]


# - 20. AI Insights Feed -

@router.post("/{ws_id}/insights/generate")
def generate_insights(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Auto-generate insights from the user active dataset and share with workspace."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset uploaded")
    insights = []
    nums = df.select_dtypes(include=np.number).columns.tolist()
    cats = df.select_dtypes(include="object").columns.tolist()
    # Auto-generate statistical insights
    for col in nums[:4]:
        mean = float(df[col].mean())
        std = float(df[col].std())
        mx = float(df[col].max())
        mn = float(df[col].min())
        insights.append(f"{col}: avg={mean:.2f}, std={std:.2f}, range=[{mn:.2f}, {mx:.2f}]")
    if len(nums) >= 2:
        corr = df[nums[:6]].corr()
        for i, c1 in enumerate(nums[:6]):
            for j, c2 in enumerate(nums[:6]):
                if i < j and abs(corr.loc[c1, c2]) > 0.7:
                    insights.append(f"Strong correlation ({corr.loc[c1,c2]:.2f}) between {c1} and {c2}")
    for col in cats[:2]:
        top = df[col].value_counts().head(1)
        if len(top):
            insights.append(f"Most common {col}: '{top.index[0]}' ({top.values[0]} occurrences)")
    # Missing values
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if len(missing_cols):
        insights.append(f"Missing values in: {', '.join(missing_cols.index.tolist()[:3])}")
    else:
        insights.append("Dataset is complete - no missing values detected")
    # Save to workspace feed
    new_insights = []
    for text in insights:
        item = {
            "id": len(_insights.get(ws_id, [])) + len(new_insights) + 1,
            "text": text, "source": user["email"],
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        new_insights.append(item)
    _insights[ws_id].extend(new_insights)
    if len(_insights[ws_id]) > 100:
        _insights[ws_id] = _insights[ws_id][-100:]
    _log_activity(ws_id, user["email"], "insights_generated", f"{len(new_insights)} insights added")
    return {"insights": new_insights, "total_added": len(new_insights)}


@router.get("/{ws_id}/insights")
def get_insights(ws_id: int, limit: int = 30,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    items = list(reversed(_insights.get(ws_id, [])))[:limit]
    return {"insights": items, "total": len(_insights.get(ws_id, []))}


# - 21. Member Leaderboard -

@router.get("/{ws_id}/leaderboard")
def get_leaderboard(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    contribs = dict(_contributions.get(ws_id, {}))
    # Also count from activity log
    for event in _activity.get(ws_id, []):
        email = event.get("user", "")
        if email:
            contribs[email] = contribs.get(email, 0) + 1
    # Deduplicate and sort
    merged: dict = {}
    for email, count in contribs.items():
        merged[email] = merged.get(email, 0) + count
    board = sorted([{"email": e, "contributions": c, "rank": 0} for e, c in merged.items()],
                   key=lambda x: x["contributions"], reverse=True)
    for i, entry in enumerate(board):
        entry["rank"] = i + 1
        entry["badge"] = "-" if i == 0 else "-" if i == 1 else "-" if i == 2 else "-"
    return {"leaderboard": board, "your_rank": next((e["rank"] for e in board if e["email"] == user["email"]), None)}


# - 22. Workspace Webhooks -

class WebhookCreate(BaseModel):
    url: str
    events: list = ["all"]   # all | chat_message | dataset_shared | task_created | alert_triggered
    secret: str = ""


@router.get("/{ws_id}/webhooks")
def list_webhooks(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can manage webhooks")
    hooks = _webhooks.get(ws_id, [])
    # Mask secret
    return {"webhooks": [{**h, "secret": "***" if h.get("secret") else ""} for h in hooks]}


@router.post("/{ws_id}/webhooks")
def create_webhook(ws_id: int, data: WebhookCreate,
                   user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_webhook_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can create webhooks")
    if not data.url.startswith("http"):
        raise HTTPException(400, "URL must start with http:// or https://")
    hook = {
        "id": _next_webhook_id, "url": data.url,
        "events": data.events, "secret": data.secret,
        "active": True, "created_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "delivery_count": 0, "last_delivery": None,
    }
    _next_webhook_id += 1
    _webhooks[ws_id].append(hook)
    _log_activity(ws_id, user["email"], "webhook_created", data.url[:50])
    return {**hook, "secret": "***" if hook["secret"] else ""}


@router.post("/{ws_id}/webhooks/{hook_id}/test")
async def test_webhook(ws_id: int, hook_id: int,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a test payload to the webhook URL."""
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can test webhooks")
    hook = next((h for h in _webhooks.get(ws_id, []) if h["id"] == hook_id), None)
    if not hook:
        raise HTTPException(404, "Webhook not found")
    payload = {"event": "test", "workspace_id": ws_id, "ts": datetime.now(timezone.utc).isoformat(), "triggered_by": user["email"]}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(hook["url"], json=payload)
        hook["delivery_count"] = hook.get("delivery_count", 0) + 1
        hook["last_delivery"] = datetime.now(timezone.utc).isoformat()
        return {"status": "delivered", "response_code": resp.status_code}
    except Exception as e:
        return {"status": "failed", "error": str(e)[:100]}


@router.delete("/{ws_id}/webhooks/{hook_id}", status_code=204)
def delete_webhook(ws_id: int, hook_id: int,
                   user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete webhooks")
    _webhooks[ws_id] = [h for h in _webhooks.get(ws_id, []) if h["id"] != hook_id]


# - 23. Dataset Versioning -

class VersionTag(BaseModel):
    tag: str = ""
    note: str = ""


@router.post("/{ws_id}/versions/snapshot")
def snapshot_dataset(ws_id: int, data: VersionTag,
                     user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save a versioned snapshot of the current dataset."""
    global _next_version_id
    role = _get_member_role(ws_id, user["email"], db)
    if not role or role == "viewer":
        raise HTTPException(403, "Viewers cannot create snapshots")
    from app.services.data_store import get as get_df, save as save_df
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset uploaded")
    version_name = f"v{_next_version_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    # Save as a named dataset in the workspace shared store
    _shared_datasets[ws_id][version_name] = {
        "name": version_name, "uploader": user["email"],
        "rows": len(df), "cols": len(df.columns),
        "columns": list(df.columns),
        "ts": datetime.now(timezone.utc).isoformat(),
        "is_version": True,
    }
    version = {
        "id": _next_version_id, "name": version_name,
        "rows": len(df), "cols": len(df.columns),
        "tag": data.tag, "note": data.note,
        "saved_by": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_version_id += 1
    _versions[ws_id].append(version)
    _log_activity(ws_id, user["email"], "version_snapshot", f"Snapshot '{version_name}' ({len(df)} rows)")
    return version


@router.get("/{ws_id}/versions")
def list_versions(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"versions": list(reversed(_versions.get(ws_id, [])))}


@router.post("/{ws_id}/versions/{version_id}/restore")
def restore_version(ws_id: int, version_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Restore a dataset version as the user active dataset."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    version = next((v for v in _versions.get(ws_id, []) if v["id"] == version_id), None)
    if not version:
        raise HTTPException(404, "Version not found")
    ds = _shared_datasets.get(ws_id, {}).get(version["name"])
    if not ds:
        raise HTTPException(404, "Version data no longer available")
    from app.services.data_store import get as get_df, save as save_df
    uploader_df = get_df(ds["uploader"])
    if uploader_df is None:
        raise HTTPException(404, "Original data no longer available")
    save_df(user["email"], uploader_df, version["name"])
    _log_activity(ws_id, user["email"], "version_restored", f"Restored '{version['name']}'")
    return {"message": f"Version '{version['name']}' restored as your active dataset"}


# - 24. Workspace Goals / KPI Targets -

class GoalCreate(BaseModel):
    title: str
    metric: str
    target: float
    unit: str = ""
    deadline: str = ""


class GoalUpdate(BaseModel):
    current: float


@router.get("/{ws_id}/goals")
def list_goals(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    goals = _goals.get(ws_id, [])
    # Auto-update current values from active dataset
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(user["email"])
    for goal in goals:
        if df is not None and goal["metric"] in df.columns:
            goal["current"] = round(float(df[goal["metric"]].mean()), 3)
            goal["progress"] = round(min(100, goal["current"] / goal["target"] * 100), 1) if goal["target"] else 0
        else:
            goal.setdefault("current", 0)
            goal.setdefault("progress", 0)
    return {"goals": goals}


@router.post("/{ws_id}/goals")
def create_goal(ws_id: int, data: GoalCreate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_goal_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create goals")
    goal = {
        "id": _next_goal_id, "title": data.title,
        "metric": data.metric, "target": data.target,
        "current": 0, "unit": data.unit, "deadline": data.deadline,
        "created_by": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
        "progress": 0,
    }
    _next_goal_id += 1
    _goals[ws_id].append(goal)
    _log_activity(ws_id, user["email"], "goal_created", f"'{data.title}' target={data.target}{data.unit}")
    return goal


@router.patch("/{ws_id}/goals/{goal_id}")
def update_goal_progress(ws_id: int, goal_id: int, data: GoalUpdate,
                         user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    goal = next((g for g in _goals.get(ws_id, []) if g["id"] == goal_id), None)
    if not goal:
        raise HTTPException(404, "Goal not found")
    goal["current"] = data.current
    goal["progress"] = round(min(100, data.current / goal["target"] * 100), 1) if goal["target"] else 0
    goal["updated_by"] = user["email"]
    _log_activity(ws_id, user["email"], "goal_updated", f"'{goal['title']}' progress={goal['progress']}%")
    return goal


@router.delete("/{ws_id}/goals/{goal_id}", status_code=204)
def delete_goal(ws_id: int, goal_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete goals")
    _goals[ws_id] = [g for g in _goals.get(ws_id, []) if g["id"] != goal_id]



# - Advanced Workspace Features Batch 3 -

_notebooks: dict = {}        # ws_id -> {id: {id,title,content,author,ts,updated}}
_tasks: dict = {}            # ws_id -> {id: {id,title,desc,status,assignee,priority,ts}}
_ws_alerts: dict = {}        # ws_id -> {id: {id,col,op,threshold,label,active,ts}}
_goals: dict = {}            # ws_id -> {id: {id,metric,target,current,unit,ts}}
_webhooks: dict = {}         # ws_id -> {id: {id,url,events,active,ts}}
_versions: dict = {}         # ws_id -> [{version,name,rows,cols,ts,uploaded_by}]
_reactions: dict = {}        # ws_id -> {msg_id: {emoji: [users]}}

_next_nb_id = 1
_next_task_id = 1
_next_ws_alert_id = 1
_next_goal_id = 1
_next_webhook_id = 1
_next_version = 1


# - 17. Workspace Notebooks -

class NotebookCreate(BaseModel):
    title: str
    content: str = ""


class NotebookUpdate(BaseModel):
    title: str = ""
    content: str = ""


@router.get("/{ws_id}/notebooks")
def list_notebooks(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"notebooks": list(_notebooks.get(ws_id, {}).values())}


@router.post("/{ws_id}/notebooks")
def create_notebook(ws_id: int, data: NotebookCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_nb_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create notebooks")
    nb = {
        "id": _next_nb_id, "title": data.title, "content": data.content,
        "author": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(), "updated_by": user["email"],
    }
    _next_nb_id += 1
    if ws_id not in _notebooks:
        _notebooks[ws_id] = {}
    _notebooks[ws_id][nb["id"]] = nb
    _log_activity(ws_id, user["email"], "notebook_created", f"Created notebook '{data.title}'")
    return nb


@router.get("/{ws_id}/notebooks/{nb_id}")
def get_notebook(ws_id: int, nb_id: int,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    nb = _notebooks.get(ws_id, {}).get(nb_id)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    return nb


@router.patch("/{ws_id}/notebooks/{nb_id}")
def update_notebook(ws_id: int, nb_id: int, data: NotebookUpdate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot edit notebooks")
    nb = _notebooks.get(ws_id, {}).get(nb_id)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    if data.title:
        nb["title"] = data.title
    if data.content is not None:
        nb["content"] = data.content
    nb["updated"] = datetime.now(timezone.utc).isoformat()
    nb["updated_by"] = user["email"]
    _log_activity(ws_id, user["email"], "notebook_updated", f"Updated '{nb['title']}'")
    return nb


@router.delete("/{ws_id}/notebooks/{nb_id}", status_code=204)
def delete_notebook(ws_id: int, nb_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    nb = _notebooks.get(ws_id, {}).get(nb_id)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    if nb["author"] != user["email"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others notebooks")
    del _notebooks[ws_id][nb_id]


# - 18. Task Board (Kanban) -

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"       # todo | in_progress | review | done
    assignee: str = ""
    priority: str = "medium"   # low | medium | high | critical


class TaskUpdate(BaseModel):
    title: str = ""
    description: str = ""
    status: str = ""
    assignee: str = ""
    priority: str = ""


@router.get("/{ws_id}/tasks")
def list_tasks(ws_id: int, status: str = "",
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    tasks = list(_tasks.get(ws_id, {}).values())
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    # Group by status for kanban view
    board = {"todo": [], "in_progress": [], "review": [], "done": []}
    for t in tasks:
        board.setdefault(t["status"], []).append(t)
    return {"tasks": tasks, "board": board}


@router.post("/{ws_id}/tasks")
def create_task(ws_id: int, data: TaskCreate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_task_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create tasks")
    task = {
        "id": _next_task_id, "title": data.title, "description": data.description,
        "status": data.status, "assignee": data.assignee, "priority": data.priority,
        "created_by": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    _next_task_id += 1
    if ws_id not in _tasks:
        _tasks[ws_id] = {}
    _tasks[ws_id][task["id"]] = task
    _log_activity(ws_id, user["email"], "task_created", f"'{data.title}' [{data.priority}]")
    return task


@router.patch("/{ws_id}/tasks/{task_id}")
def update_task(ws_id: int, task_id: int, data: TaskUpdate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    task = _tasks.get(ws_id, {}).get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    old_status = task["status"]
    if data.title:
        task["title"] = data.title
    if data.description is not None:
        task["description"] = data.description
    if data.status:
        task["status"] = data.status
    if data.assignee is not None:
        task["assignee"] = data.assignee
    if data.priority:
        task["priority"] = data.priority
    task["updated"] = datetime.now(timezone.utc).isoformat()
    if data.status and data.status != old_status:
        _log_activity(ws_id, user["email"], "task_moved",
                      f"'{task['title']}' {old_status} -> {data.status}")
    return task


@router.delete("/{ws_id}/tasks/{task_id}", status_code=204)
def delete_task(ws_id: int, task_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    task = _tasks.get(ws_id, {}).get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["created_by"] != user["email"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others tasks")
    del _tasks[ws_id][task_id]


# - 19. Workspace Goals / KPI Targets -

class GoalCreate(BaseModel):
    metric: str
    target: float
    current: float = 0.0
    unit: str = ""
    description: str = ""


class GoalUpdate(BaseModel):
    current: float


@router.get("/{ws_id}/goals")
def list_goals(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    goals = list(_goals.get(ws_id, {}).values())
    for g in goals:
        g["progress"] = round(min(100, (g["current"] / g["target"] * 100)) if g["target"] else 0, 1)
        g["status"] = "achieved" if g["current"] >= g["target"] else "on_track" if g["progress"] >= 70 else "at_risk"
    return {"goals": goals}


@router.post("/{ws_id}/goals")
def create_goal(ws_id: int, data: GoalCreate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_goal_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create goals")
    goal = {
        "id": _next_goal_id, "metric": data.metric, "target": data.target,
        "current": data.current, "unit": data.unit, "description": data.description,
        "created_by": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_goal_id += 1
    if ws_id not in _goals:
        _goals[ws_id] = {}
    _goals[ws_id][goal["id"]] = goal
    _log_activity(ws_id, user["email"], "goal_created", f"'{data.metric}' target={data.target}{data.unit}")
    return goal


@router.patch("/{ws_id}/goals/{goal_id}")
def update_goal_progress(ws_id: int, goal_id: int, data: GoalUpdate,
                         user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    goal = _goals.get(ws_id, {}).get(goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    old = goal["current"]
    goal["current"] = data.current
    _log_activity(ws_id, user["email"], "goal_updated",
                  f"'{goal['metric']}' {old} -> {data.current}{goal['unit']}")
    return goal


@router.delete("/{ws_id}/goals/{goal_id}", status_code=204)
def delete_goal(ws_id: int, goal_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete goals")
    if goal_id in _goals.get(ws_id, {}):
        del _goals[ws_id][goal_id]


# - 20. Workspace Webhooks -

class WebhookCreate(BaseModel):
    url: str
    events: list = ["dataset_shared", "chat_message", "task_moved", "announcement_posted"]
    secret: str = ""


@router.get("/{ws_id}/webhooks")
def list_webhooks(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can manage webhooks")
    hooks = list(_webhooks.get(ws_id, {}).values())
    # Mask secret
    for h in hooks:
        if h.get("secret"):
            h["secret"] = "***"
    return {"webhooks": hooks}


@router.post("/{ws_id}/webhooks")
def create_webhook(ws_id: int, data: WebhookCreate,
                   user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_webhook_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can create webhooks")
    hook = {
        "id": _next_webhook_id, "url": data.url, "events": data.events,
        "secret": data.secret, "active": True,
        "created_by": user["email"], "ts": datetime.now(timezone.utc).isoformat(),
        "deliveries": 0, "last_delivery": None,
    }
    _next_webhook_id += 1
    if ws_id not in _webhooks:
        _webhooks[ws_id] = {}
    _webhooks[ws_id][hook["id"]] = hook
    _log_activity(ws_id, user["email"], "webhook_created", f"URL: {data.url[:40]}")
    return {**hook, "secret": "***" if hook["secret"] else ""}


@router.post("/{ws_id}/webhooks/{hook_id}/test")
async def test_webhook(ws_id: int, hook_id: int,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can test webhooks")
    hook = _webhooks.get(ws_id, {}).get(hook_id)
    if not hook:
        raise HTTPException(404, "Webhook not found")
    import httpx
    payload = {"event": "test", "workspace_id": ws_id, "ts": datetime.now(timezone.utc).isoformat()}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(hook["url"], json=payload)
        hook["deliveries"] = hook.get("deliveries", 0) + 1
        hook["last_delivery"] = datetime.now(timezone.utc).isoformat()
        return {"status": resp.status_code, "message": "Test delivered"}
    except Exception as e:
        return {"status": 0, "message": f"Delivery failed: {str(e)[:60]}"}


@router.delete("/{ws_id}/webhooks/{hook_id}", status_code=204)
def delete_webhook(ws_id: int, hook_id: int,
                   user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete webhooks")
    if hook_id in _webhooks.get(ws_id, {}):
        del _webhooks[ws_id][hook_id]


# - 21. Dataset Versioning -

@router.get("/{ws_id}/versions")
def list_versions(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"versions": list(reversed(_versions.get(ws_id, [])))}


@router.post("/{ws_id}/versions/snapshot")
def snapshot_dataset(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save a version snapshot of the current active dataset."""
    global _next_version
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create snapshots")
    from app.services.data_store import get as get_df, save as save_df
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No active dataset to snapshot")
    version_name = f"v{_next_version}"
    snap = {
        "version": version_name, "version_num": _next_version,
        "rows": len(df), "cols": len(df.columns),
        "columns": list(df.columns),
        "uploaded_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }
    _next_version += 1
    if ws_id not in _versions:
        _versions[ws_id] = []
    _versions[ws_id].append(snap)
    # Also share to workspace datasets
    _shared_datasets[ws_id][version_name] = {
        "name": version_name, "uploader": user["email"],
        "rows": len(df), "cols": len(df.columns),
        "columns": list(df.columns),
        "ts": snap["ts"],
    }
    _log_activity(ws_id, user["email"], "version_snapshot",
                  f"Snapshot {version_name}: {len(df)} rows")
    return snap


# - 22. Member Leaderboard -

@router.get("/{ws_id}/leaderboard")
def get_leaderboard(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    events = _activity.get(ws_id, [])
    # Score by event type
    SCORES = {
        "dataset_shared": 10, "version_snapshot": 8, "chart_pinned": 5,
        "query_saved": 4, "query_run": 2, "notebook_created": 6,
        "notebook_updated": 3, "task_created": 4, "task_moved": 2,
        "chat_message": 1, "announcement_posted": 5, "goal_created": 6,
        "goal_updated": 2,
    }
    scores: dict = {}
    event_counts: dict = {}
    for e in events:
        u = e["user"]
        pts = SCORES.get(e["event"], 1)
        scores[u] = scores.get(u, 0) + pts
        if u not in event_counts:
            event_counts[u] = {}
        event_counts[u][e["event"]] = event_counts[u].get(e["event"], 0) + 1
    board = sorted(
        [{"email": u, "score": s, "rank": 0, "events": event_counts.get(u, {})}
         for u, s in scores.items()],
        key=lambda x: x["score"], reverse=True
    )
    for i, entry in enumerate(board):
        entry["rank"] = i + 1
        entry["badge"] = "-" if i == 0 else "-" if i == 1 else "-" if i == 2 else "-"
    return {"leaderboard": board}


# - 23. Chat Reactions -

class ReactionAdd(BaseModel):
    emoji: str


@router.post("/{ws_id}/chat/{msg_id}/react")
def add_reaction(ws_id: int, msg_id: int, data: ReactionAdd,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    if ws_id not in _reactions:
        _reactions[ws_id] = {}
    if msg_id not in _reactions[ws_id]:
        _reactions[ws_id][msg_id] = {}
    emoji = data.emoji
    if emoji not in _reactions[ws_id][msg_id]:
        _reactions[ws_id][msg_id][emoji] = []
    users = _reactions[ws_id][msg_id][emoji]
    if user["email"] in users:
        users.remove(user["email"])  # toggle off
    else:
        users.append(user["email"])  # toggle on
    return {"reactions": _reactions[ws_id][msg_id]}


@router.get("/{ws_id}/chat/{msg_id}/reactions")
def get_reactions(ws_id: int, msg_id: int,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"reactions": _reactions.get(ws_id, {}).get(msg_id, {})}


# - 24. Workspace Summary (AI-powered) -

@router.get("/{ws_id}/summary")
def workspace_summary(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a comprehensive workspace summary."""
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws_id).all()
    events = _activity.get(ws_id, [])
    tasks = list(_tasks.get(ws_id, {}).values())
    goals = list(_goals.get(ws_id, {}).values())
    now = datetime.now(timezone.utc)
    cutoff_7d = (now - timedelta(days=7)).isoformat()
    recent_events = [e for e in events if e["ts"] > cutoff_7d]
    task_stats = {
        "total": len(tasks),
        "todo": sum(1 for t in tasks if t["status"] == "todo"),
        "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
        "done": sum(1 for t in tasks if t["status"] == "done"),
    }
    goal_stats = []
    for g in goals:
        pct = min(100, (g["current"] / g["target"] * 100)) if g["target"] else 0
        goal_stats.append({"metric": g["metric"], "progress": round(pct, 1),
                           "status": "achieved" if pct >= 100 else "on_track" if pct >= 70 else "at_risk"})
    return {
        "workspace": {"id": ws_id, "name": ws.name if ws else "", "description": ws.description if ws else ""},
        "members": len(members) + 1,
        "activity_7d": len(recent_events),
        "shared_datasets": len(_shared_datasets.get(ws_id, {})),
        "pinned_charts": len(_pinned.get(ws_id, [])),
        "notebooks": len(_notebooks.get(ws_id, {})),
        "tasks": task_stats,
        "goals": goal_stats,
        "versions": len(_versions.get(ws_id, [])),
        "announcements": len(_announcements.get(ws_id, [])),
        "saved_queries": len(_saved_queries.get(ws_id, [])),
        "webhooks": len(_webhooks.get(ws_id, {})),
        "top_contributors": sorted(
            [{"email": k, "events": v} for k, v in
             {e["user"]: sum(1 for x in events if x["user"] == e["user"]) for e in events}.items()],
            key=lambda x: x["events"], reverse=True
        )[:3],
    }



# Advanced Workspace Features Batch 4

_polls = {}          # ws_id -> {id: {id,question,options,votes,created_by,ts,closed}}
_contracts = {}      # ws_id -> {id: {id,name,schema,owner,ts,status}}
_integrations = {}   # ws_id -> {id: {id,type,config,active,ts}}
_permissions = {}    # ws_id -> {user_email: {feature: bool}}
_changelog = {}      # ws_id -> [{id,version,title,body,author,ts}]
_metrics_board = {}  # ws_id -> [{id,name,value,unit,trend,ts}]

_next_poll_id = 1
_next_contract_id = 1
_next_integration_id = 1
_next_changelog_id = 1
_next_metric_id = 1


# 25. Workspace Polls
class PollCreate(BaseModel):
    question: str
    options: list


class PollVote(BaseModel):
    option: str


@router.get("/{ws_id}/polls")
def list_polls(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    polls = list(_polls.get(ws_id, {}).values())
    for p in polls:
        p["total_votes"] = sum(len(v) for v in p["votes"].values())
        p["user_voted"] = any(user["email"] in v for v in p["votes"].values())
    return {"polls": polls}


@router.post("/{ws_id}/polls")
def create_poll(ws_id: int, data: PollCreate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_poll_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create polls")
    poll = {
        "id": _next_poll_id, "question": data.question,
        "options": data.options,
        "votes": {opt: [] for opt in data.options},
        "created_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "closed": False,
    }
    _next_poll_id += 1
    if ws_id not in _polls:
        _polls[ws_id] = {}
    _polls[ws_id][poll["id"]] = poll
    _log_activity(ws_id, user["email"], "poll_created", f"'{data.question}'")
    return poll


@router.post("/{ws_id}/polls/{poll_id}/vote")
def vote_poll(ws_id: int, poll_id: int, data: PollVote,
              user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    poll = _polls.get(ws_id, {}).get(poll_id)
    if not poll:
        raise HTTPException(404, "Poll not found")
    if poll["closed"]:
        raise HTTPException(400, "Poll is closed")
    if data.option not in poll["votes"]:
        raise HTTPException(400, "Invalid option")
    # Remove previous vote
    for opt_voters in poll["votes"].values():
        if user["email"] in opt_voters:
            opt_voters.remove(user["email"])
    poll["votes"][data.option].append(user["email"])
    _log_activity(ws_id, user["email"], "poll_voted", f"Voted '{data.option}'")
    return {"votes": poll["votes"], "total": sum(len(v) for v in poll["votes"].values())}


@router.post("/{ws_id}/polls/{poll_id}/close")
def close_poll(ws_id: int, poll_id: int,
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can close polls")
    poll = _polls.get(ws_id, {}).get(poll_id)
    if not poll:
        raise HTTPException(404, "Poll not found")
    poll["closed"] = True
    winner = max(poll["votes"], key=lambda k: len(poll["votes"][k])) if poll["votes"] else None
    _log_activity(ws_id, user["email"], "poll_closed", f"Winner: '{winner}'")
    return {"message": "Poll closed", "winner": winner}


@router.delete("/{ws_id}/polls/{poll_id}", status_code=204)
def delete_poll(ws_id: int, poll_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete polls")
    if poll_id in _polls.get(ws_id, {}):
        del _polls[ws_id][poll_id]


# 26. Data Contracts
class ContractCreate(BaseModel):
    name: str
    description: str = ""
    schema_def: dict = {}   # {column: {type, required, description}}
    sla: str = ""           # e.g. "Updated daily by 9am"


@router.get("/{ws_id}/contracts")
def list_contracts(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"contracts": list(_contracts.get(ws_id, {}).values())}


@router.post("/{ws_id}/contracts")
def create_contract(ws_id: int, data: ContractCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_contract_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create contracts")
    contract = {
        "id": _next_contract_id, "name": data.name,
        "description": data.description, "schema_def": data.schema_def,
        "sla": data.sla, "owner": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "active", "violations": [],
    }
    _next_contract_id += 1
    if ws_id not in _contracts:
        _contracts[ws_id] = {}
    _contracts[ws_id][contract["id"]] = contract
    _log_activity(ws_id, user["email"], "contract_created", f"'{data.name}'")
    return contract


@router.post("/{ws_id}/contracts/{contract_id}/validate")
def validate_contract(ws_id: int, contract_id: int,
                      user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    contract = _contracts.get(ws_id, {}).get(contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    from app.services.data_store import get as get_df
    df = get_df(user["email"])
    if df is None:
        return {"valid": False, "violations": ["No dataset loaded"]}
    violations = []
    schema = contract.get("schema_def", {})
    for col, rules in schema.items():
        if rules.get("required") and col not in df.columns:
            violations.append(f"Missing required column: {col}")
        elif col in df.columns:
            expected_type = rules.get("type", "")
            if expected_type == "numeric" and not hasattr(df[col], "dtype"):
                violations.append(f"Column {col} should be numeric")
    contract["violations"] = violations
    contract["last_validated"] = datetime.now(timezone.utc).isoformat()
    contract["status"] = "valid" if not violations else "violated"
    _log_activity(ws_id, user["email"], "contract_validated",
                  f"'{contract['name']}': {'valid' if not violations else str(len(violations)) + ' violations'}")
    return {"valid": not violations, "violations": violations}


@router.delete("/{ws_id}/contracts/{contract_id}", status_code=204)
def delete_contract(ws_id: int, contract_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete contracts")
    if contract_id in _contracts.get(ws_id, {}):
        del _contracts[ws_id][contract_id]


# 27. Workspace Integrations
class IntegrationCreate(BaseModel):
    type: str       # slack | teams | discord | email | custom
    name: str = ""
    webhook_url: str = ""
    events: list = ["announcement_posted", "dataset_shared", "task_moved"]
    config: dict = {}


@router.get("/{ws_id}/integrations")
def list_integrations(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can view integrations")
    intgs = list(_integrations.get(ws_id, {}).values())
    for i in intgs:
        if i.get("webhook_url"):
            i["webhook_url"] = i["webhook_url"][:30] + "***"
    return {"integrations": intgs}


@router.post("/{ws_id}/integrations")
def create_integration(ws_id: int, data: IntegrationCreate,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_integration_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can add integrations")
    if data.type not in ("slack", "teams", "discord", "email", "custom"):
        raise HTTPException(400, "Invalid integration type")
    intg = {
        "id": _next_integration_id, "type": data.type,
        "name": data.name or data.type.title(),
        "webhook_url": data.webhook_url, "events": data.events,
        "config": data.config, "active": True,
        "created_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "deliveries": 0,
    }
    _next_integration_id += 1
    if ws_id not in _integrations:
        _integrations[ws_id] = {}
    _integrations[ws_id][intg["id"]] = intg
    _log_activity(ws_id, user["email"], "integration_added", f"{data.type}: {data.name}")
    return {**intg, "webhook_url": intg["webhook_url"][:30] + "***" if intg["webhook_url"] else ""}


@router.post("/{ws_id}/integrations/{intg_id}/test")
async def test_integration(ws_id: int, intg_id: int,
                           user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can test integrations")
    intg = _integrations.get(ws_id, {}).get(intg_id)
    if not intg:
        raise HTTPException(404, "Integration not found")
    if not intg.get("webhook_url"):
        return {"status": "skipped", "message": "No webhook URL configured"}
    import httpx
    payload = {"text": f"Test from COGNIDATA workspace {ws_id}", "event": "test"}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(intg["webhook_url"], json=payload)
        intg["deliveries"] = intg.get("deliveries", 0) + 1
        return {"status": resp.status_code, "message": "Test sent"}
    except Exception as e:
        return {"status": 0, "message": str(e)[:60]}


@router.delete("/{ws_id}/integrations/{intg_id}", status_code=204)
def delete_integration(ws_id: int, intg_id: int,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete integrations")
    if intg_id in _integrations.get(ws_id, {}):
        del _integrations[ws_id][intg_id]


# 28. Permissions Matrix
class PermissionUpdate(BaseModel):
    user_email: str
    permissions: dict   # {feature: bool}


FEATURES = ["chat", "datasets", "pins", "queries", "notebooks", "tasks",
            "goals", "reports", "announcements", "polls", "contracts"]


@router.get("/{ws_id}/permissions")
def get_permissions(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can view permissions")
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws_id).all()
    result = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            perms = _permissions.get(ws_id, {}).get(u.email, {})
            # Default: editors get all, viewers get read-only
            defaults = {f: True for f in FEATURES} if m.role in ("editor", "admin") else {f: False for f in FEATURES}
            result.append({
                "email": u.email, "role": m.role,
                "permissions": {**defaults, **perms},
            })
    return {"matrix": result, "features": FEATURES}


@router.patch("/{ws_id}/permissions")
def update_permissions(ws_id: int, data: PermissionUpdate,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can update permissions")
    if ws_id not in _permissions:
        _permissions[ws_id] = {}
    if data.user_email not in _permissions[ws_id]:
        _permissions[ws_id][data.user_email] = {}
    _permissions[ws_id][data.user_email].update(data.permissions)
    _log_activity(ws_id, user["email"], "permissions_updated",
                  f"Updated permissions for {data.user_email}")
    return {"message": "Permissions updated", "permissions": _permissions[ws_id][data.user_email]}


# 29. Workspace Changelog
class ChangelogEntry(BaseModel):
    version: str
    title: str
    body: str
    breaking: bool = False


@router.get("/{ws_id}/changelog")
def list_changelog(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"changelog": list(reversed(_changelog.get(ws_id, [])))}


@router.post("/{ws_id}/changelog")
def add_changelog(ws_id: int, data: ChangelogEntry,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_changelog_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot add changelog entries")
    entry = {
        "id": _next_changelog_id, "version": data.version,
        "title": data.title, "body": data.body,
        "breaking": data.breaking, "author": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_changelog_id += 1
    if ws_id not in _changelog:
        _changelog[ws_id] = []
    _changelog[ws_id].append(entry)
    _log_activity(ws_id, user["email"], "changelog_added",
                  f"v{data.version}: {data.title}")
    return entry


@router.delete("/{ws_id}/changelog/{entry_id}", status_code=204)
def delete_changelog(ws_id: int, entry_id: int,
                     user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete changelog entries")
    _changelog[ws_id] = [e for e in _changelog.get(ws_id, []) if e["id"] != entry_id]


# 30. Metrics Dashboard
class MetricCreate(BaseModel):
    name: str
    value: float
    unit: str = ""
    trend: str = "stable"   # up | down | stable


@router.get("/{ws_id}/metrics")
def list_metrics(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"metrics": list(_metrics_board.get(ws_id, {}).values())}


@router.post("/{ws_id}/metrics")
def add_metric(ws_id: int, data: MetricCreate,
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_metric_id
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot add metrics")
    metric = {
        "id": _next_metric_id, "name": data.name,
        "value": data.value, "unit": data.unit, "trend": data.trend,
        "updated_by": user["email"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "history": [{"value": data.value, "ts": datetime.now(timezone.utc).isoformat()}],
    }
    _next_metric_id += 1
    if ws_id not in _metrics_board:
        _metrics_board[ws_id] = {}
    _metrics_board[ws_id][metric["id"]] = metric
    _log_activity(ws_id, user["email"], "metric_added", f"'{data.name}' = {data.value}{data.unit}")
    return metric


@router.patch("/{ws_id}/metrics/{metric_id}")
def update_metric(ws_id: int, metric_id: int, data: MetricCreate,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    metric = _metrics_board.get(ws_id, {}).get(metric_id)
    if not metric:
        raise HTTPException(404, "Metric not found")
    old_val = metric["value"]
    metric["value"] = data.value
    metric["trend"] = "up" if data.value > old_val else "down" if data.value < old_val else "stable"
    metric["updated_by"] = user["email"]
    metric["ts"] = datetime.now(timezone.utc).isoformat()
    metric["history"].append({"value": data.value, "ts": metric["ts"]})
    if len(metric["history"]) > 30:
        metric["history"] = metric["history"][-30:]
    return metric


@router.delete("/{ws_id}/metrics/{metric_id}", status_code=204)
def delete_metric(ws_id: int, metric_id: int,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete metrics")
    if metric_id in _metrics_board.get(ws_id, {}):
        del _metrics_board[ws_id][metric_id]


# 31. Workspace Backup & Restore
import json as _json_mod

@router.get("/{ws_id}/backup")
def backup_workspace(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can backup workspace")
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    backup = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": user["email"],
        "workspace": {"id": ws_id, "name": ws.name if ws else "", "description": ws.description if ws else ""},
        "pins": _pinned.get(ws_id, []),
        "queries": _saved_queries.get(ws_id, []),
        "announcements": _announcements.get(ws_id, []),
        "notebooks": list(_notebooks.get(ws_id, {}).values()),
        "tasks": list(_tasks.get(ws_id, {}).values()),
        "goals": list(_goals.get(ws_id, {}).values()),
        "changelog": _changelog.get(ws_id, []),
        "metrics": list(_metrics_board.get(ws_id, {}).values()),
        "settings": _ws_settings.get(ws_id, {}),
        "activity_count": len(_activity.get(ws_id, [])),
    }
    _log_activity(ws_id, user["email"], "workspace_backup", "Full backup exported")
    return StreamingResponse(
        iter([_json_mod.dumps(backup, indent=2, default=str)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=workspace_{ws_id}_backup.json"},
    )


class RestoreData(BaseModel):
    backup: dict


@router.post("/{ws_id}/restore")
def restore_workspace(ws_id: int, data: RestoreData,
                      user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if role != "owner":
        raise HTTPException(403, "Only owner can restore workspace")
    b = data.backup
    if b.get("version") != "1.0":
        raise HTTPException(400, "Unsupported backup version")
    restored = []
    if "pins" in b:
        _pinned[ws_id] = b["pins"]; restored.append(f"{len(b['pins'])} pins")
    if "queries" in b:
        _saved_queries[ws_id] = b["queries"]; restored.append(f"{len(b['queries'])} queries")
    if "notebooks" in b:
        _notebooks[ws_id] = {nb["id"]: nb for nb in b["notebooks"]}; restored.append(f"{len(b['notebooks'])} notebooks")
    if "tasks" in b:
        _tasks[ws_id] = {t["id"]: t for t in b["tasks"]}; restored.append(f"{len(b['tasks'])} tasks")
    if "goals" in b:
        _goals[ws_id] = {g["id"]: g for g in b["goals"]}; restored.append(f"{len(b['goals'])} goals")
    if "changelog" in b:
        _changelog[ws_id] = b["changelog"]; restored.append(f"{len(b['changelog'])} changelog entries")
    if "metrics" in b:
        _metrics_board[ws_id] = {m["id"]: m for m in b["metrics"]}; restored.append(f"{len(b['metrics'])} metrics")
    if "settings" in b:
        _ws_settings[ws_id] = b["settings"]
    _log_activity(ws_id, user["email"], "workspace_restored", f"Restored: {', '.join(restored)}")
    return {"message": "Workspace restored", "restored": restored}


# 32. Workspace Digest (AI-powered weekly summary)
@router.get("/{ws_id}/digest")
def get_digest(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["email"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=7)).isoformat()
    events = [e for e in _activity.get(ws_id, []) if e["ts"] > cutoff]
    tasks = list(_tasks.get(ws_id, {}).values())
    goals = list(_goals.get(ws_id, {}).values())
    polls = list(_polls.get(ws_id, {}).values())
    # Build digest sections
    completed_tasks = [t for t in tasks if t["status"] == "done"]
    active_tasks = [t for t in tasks if t["status"] in ("todo", "in_progress")]
    achieved_goals = [g for g in goals if g.get("current", 0) >= g.get("target", 1)]
    closed_polls = [p for p in polls if p.get("closed")]
    top_contributors = {}
    for e in events:
        top_contributors[e["user"]] = top_contributors.get(e["user"], 0) + 1
    top = sorted(top_contributors.items(), key=lambda x: x[1], reverse=True)[:3]
    digest = {
        "period": f"{cutoff[:10]} to {now.isoformat()[:10]}",
        "workspace": ws.name if ws else "",
        "highlights": {
            "total_events": len(events),
            "tasks_completed": len(completed_tasks),
            "tasks_active": len(active_tasks),
            "goals_achieved": len(achieved_goals),
            "polls_closed": len(closed_polls),
            "new_datasets": len([e for e in events if e["event"] == "dataset_shared"]),
            "new_notebooks": len([e for e in events if e["event"] == "notebook_created"]),
            "chat_messages": len([e for e in events if e["event"] == "chat_message"]),
        },
        "top_contributors": [{"email": e, "events": c} for e, c in top],
        "completed_tasks": [{"title": t["title"], "by": t.get("assignee", t["created_by"])} for t in completed_tasks[:5]],
        "achieved_goals": [{"metric": g["metric"], "value": g["current"], "target": g["target"]} for g in achieved_goals],
        "recent_announcements": list(reversed(_announcements.get(ws_id, [])))[:3],
        "generated_at": now.isoformat(),
    }
    return digest

