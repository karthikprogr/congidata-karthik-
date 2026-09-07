import pathlib

WS = pathlib.Path(r"D:\cogni-2-main\cognidata\backend\app\api\routes\workspaces.py")

BLOCK = '''

# ── Advanced Workspace Features Batch 3 ──────────────────────────────────────

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


# ── 17. Workspace Notebooks ───────────────────────────────────────────────────

class NotebookCreate(BaseModel):
    title: str
    content: str = ""


class NotebookUpdate(BaseModel):
    title: str = ""
    content: str = ""


@router.get("/{ws_id}/notebooks")
def list_notebooks(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"notebooks": list(_notebooks.get(ws_id, {}).values())}


@router.post("/{ws_id}/notebooks")
def create_notebook(ws_id: int, data: NotebookCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_nb_id
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create notebooks")
    nb = {
        "id": _next_nb_id, "title": data.title, "content": data.content,
        "author": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(), "updated_by": user["sub"],
    }
    _next_nb_id += 1
    if ws_id not in _notebooks:
        _notebooks[ws_id] = {}
    _notebooks[ws_id][nb["id"]] = nb
    _log_activity(ws_id, user["sub"], "notebook_created", f"Created notebook '{data.title}'")
    return nb


@router.get("/{ws_id}/notebooks/{nb_id}")
def get_notebook(ws_id: int, nb_id: int,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    nb = _notebooks.get(ws_id, {}).get(nb_id)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    return nb


@router.patch("/{ws_id}/notebooks/{nb_id}")
def update_notebook(ws_id: int, nb_id: int, data: NotebookUpdate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    nb["updated_by"] = user["sub"]
    _log_activity(ws_id, user["sub"], "notebook_updated", f"Updated '{nb['title']}'")
    return nb


@router.delete("/{ws_id}/notebooks/{nb_id}", status_code=204)
def delete_notebook(ws_id: int, nb_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    nb = _notebooks.get(ws_id, {}).get(nb_id)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    if nb["author"] != user["sub"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others notebooks")
    del _notebooks[ws_id][nb_id]


# ── 18. Task Board (Kanban) ───────────────────────────────────────────────────

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
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create tasks")
    task = {
        "id": _next_task_id, "title": data.title, "description": data.description,
        "status": data.status, "assignee": data.assignee, "priority": data.priority,
        "created_by": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    _next_task_id += 1
    if ws_id not in _tasks:
        _tasks[ws_id] = {}
    _tasks[ws_id][task["id"]] = task
    _log_activity(ws_id, user["sub"], "task_created", f"'{data.title}' [{data.priority}]")
    return task


@router.patch("/{ws_id}/tasks/{task_id}")
def update_task(ws_id: int, task_id: int, data: TaskUpdate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
        _log_activity(ws_id, user["sub"], "task_moved",
                      f"'{task['title']}' {old_status} -> {data.status}")
    return task


@router.delete("/{ws_id}/tasks/{task_id}", status_code=204)
def delete_task(ws_id: int, task_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    task = _tasks.get(ws_id, {}).get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["created_by"] != user["sub"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others tasks")
    del _tasks[ws_id][task_id]


# ── 19. Workspace Goals / KPI Targets ────────────────────────────────────────

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
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create goals")
    goal = {
        "id": _next_goal_id, "metric": data.metric, "target": data.target,
        "current": data.current, "unit": data.unit, "description": data.description,
        "created_by": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_goal_id += 1
    if ws_id not in _goals:
        _goals[ws_id] = {}
    _goals[ws_id][goal["id"]] = goal
    _log_activity(ws_id, user["sub"], "goal_created", f"'{data.metric}' target={data.target}{data.unit}")
    return goal


@router.patch("/{ws_id}/goals/{goal_id}")
def update_goal_progress(ws_id: int, goal_id: int, data: GoalUpdate,
                         user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    goal = _goals.get(ws_id, {}).get(goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    old = goal["current"]
    goal["current"] = data.current
    _log_activity(ws_id, user["sub"], "goal_updated",
                  f"'{goal['metric']}' {old} -> {data.current}{goal['unit']}")
    return goal


@router.delete("/{ws_id}/goals/{goal_id}", status_code=204)
def delete_goal(ws_id: int, goal_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete goals")
    if goal_id in _goals.get(ws_id, {}):
        del _goals[ws_id][goal_id]


# ── 20. Workspace Webhooks ────────────────────────────────────────────────────

class WebhookCreate(BaseModel):
    url: str
    events: list = ["dataset_shared", "chat_message", "task_moved", "announcement_posted"]
    secret: str = ""


@router.get("/{ws_id}/webhooks")
def list_webhooks(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can create webhooks")
    hook = {
        "id": _next_webhook_id, "url": data.url, "events": data.events,
        "secret": data.secret, "active": True,
        "created_by": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
        "deliveries": 0, "last_delivery": None,
    }
    _next_webhook_id += 1
    if ws_id not in _webhooks:
        _webhooks[ws_id] = {}
    _webhooks[ws_id][hook["id"]] = hook
    _log_activity(ws_id, user["sub"], "webhook_created", f"URL: {data.url[:40]}")
    return {**hook, "secret": "***" if hook["secret"] else ""}


@router.post("/{ws_id}/webhooks/{hook_id}/test")
async def test_webhook(ws_id: int, hook_id: int,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete webhooks")
    if hook_id in _webhooks.get(ws_id, {}):
        del _webhooks[ws_id][hook_id]


# ── 21. Dataset Versioning ────────────────────────────────────────────────────

@router.get("/{ws_id}/versions")
def list_versions(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"versions": list(reversed(_versions.get(ws_id, [])))}


@router.post("/{ws_id}/versions/snapshot")
def snapshot_dataset(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save a version snapshot of the current active dataset."""
    global _next_version
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create snapshots")
    from app.services.data_store import get as get_df, save as save_df
    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No active dataset to snapshot")
    version_name = f"v{_next_version}"
    snap = {
        "version": version_name, "version_num": _next_version,
        "rows": len(df), "cols": len(df.columns),
        "columns": list(df.columns),
        "uploaded_by": user["sub"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }
    _next_version += 1
    if ws_id not in _versions:
        _versions[ws_id] = []
    _versions[ws_id].append(snap)
    # Also share to workspace datasets
    _shared_datasets[ws_id][version_name] = {
        "name": version_name, "uploader": user["sub"],
        "rows": len(df), "cols": len(df.columns),
        "columns": list(df.columns),
        "ts": snap["ts"],
    }
    _log_activity(ws_id, user["sub"], "version_snapshot",
                  f"Snapshot {version_name}: {len(df)} rows")
    return snap


# ── 22. Member Leaderboard ────────────────────────────────────────────────────

@router.get("/{ws_id}/leaderboard")
def get_leaderboard(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
        entry["badge"] = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "⭐"
    return {"leaderboard": board}


# ── 23. Chat Reactions ────────────────────────────────────────────────────────

class ReactionAdd(BaseModel):
    emoji: str


@router.post("/{ws_id}/chat/{msg_id}/react")
def add_reaction(ws_id: int, msg_id: int, data: ReactionAdd,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    if user["sub"] in users:
        users.remove(user["sub"])  # toggle off
    else:
        users.append(user["sub"])  # toggle on
    return {"reactions": _reactions[ws_id][msg_id]}


@router.get("/{ws_id}/chat/{msg_id}/reactions")
def get_reactions(ws_id: int, msg_id: int,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"reactions": _reactions.get(ws_id, {}).get(msg_id, {})}


# ── 24. Workspace Summary (AI-powered) ───────────────────────────────────────

@router.get("/{ws_id}/summary")
def workspace_summary(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a comprehensive workspace summary."""
    role = _get_member_role(ws_id, user["sub"], db)
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

'''

with open(WS, "a", encoding="utf-8") as f:
    f.write(BLOCK)

import ast
ast.parse(open(WS, encoding="utf-8").read())
print("Syntax OK - lines:", len(open(WS, encoding="utf-8").readlines()))
