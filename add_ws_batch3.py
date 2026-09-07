import pathlib

path = pathlib.Path(r"D:\cogni-2-main\cognidata\backend\app\api\routes\workspaces.py")

BLOCK = '''

# ── Advanced Workspace Features Batch 3 ──────────────────────────────────────

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
    return {"notebooks": list(reversed(_notebooks.get(ws_id, [])))}


@router.post("/{ws_id}/notebooks")
def create_notebook(ws_id: int, data: NotebookCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_nb_id
    role = _get_member_role(ws_id, user["sub"], db)
    if not role or role == "viewer":
        raise HTTPException(403, "Viewers cannot create notebooks")
    nb = {
        "id": _next_nb_id, "title": data.title, "content": data.content,
        "author": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(), "updated_by": user["sub"],
    }
    _next_nb_id += 1
    _notebooks[ws_id].append(nb)
    _track(ws_id, user["sub"], "notebook_created")
    return nb


@router.patch("/{ws_id}/notebooks/{nb_id}")
def update_notebook(ws_id: int, nb_id: int, data: NotebookUpdate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    nb["updated_by"] = user["sub"]
    _track(ws_id, user["sub"], "notebook_updated")
    return nb


@router.delete("/{ws_id}/notebooks/{nb_id}", status_code=204)
def delete_notebook(ws_id: int, nb_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    nbs = _notebooks.get(ws_id, [])
    nb = next((n for n in nbs if n["id"] == nb_id), None)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    if nb["author"] != user["sub"] and role not in ("owner", "admin"):
        raise HTTPException(403, "Cannot delete others notebooks")
    _notebooks[ws_id] = [n for n in nbs if n["id"] != nb_id]


# ── 18. Task Board (Kanban) ───────────────────────────────────────────────────

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
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if not role or role == "viewer":
        raise HTTPException(403, "Viewers cannot create tasks")
    task = {
        "id": _next_task_id, "title": data.title, "description": data.description,
        "assignee": data.assignee, "priority": data.priority,
        "due": data.due, "status": data.status,
        "created_by": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_task_id += 1
    _tasks[ws_id].append(task)
    _track(ws_id, user["sub"], "task_created")
    return task


@router.patch("/{ws_id}/tasks/{task_id}")
def update_task(ws_id: int, task_id: int, data: TaskUpdate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    task = next((t for t in _tasks.get(ws_id, []) if t["id"] == task_id), None)
    if not task:
        raise HTTPException(404, "Task not found")
    for field in ("title", "description", "assignee", "priority", "due", "status"):
        val = getattr(data, field)
        if val:
            task[field] = val
    task["updated_by"] = user["sub"]
    task["updated_ts"] = datetime.now(timezone.utc).isoformat()
    _track(ws_id, user["sub"], "task_updated")
    return task


@router.delete("/{ws_id}/tasks/{task_id}", status_code=204)
def delete_task(ws_id: int, task_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _tasks[ws_id] = [t for t in _tasks.get(ws_id, []) if t["id"] != task_id]


# ── 19. Workspace Data Alerts ─────────────────────────────────────────────────

class WsAlertCreate(BaseModel):
    metric: str
    threshold: float
    condition: str = "above"   # above | below | equals
    notify_all: bool = True


@router.get("/{ws_id}/data-alerts")
def list_ws_alerts(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"alerts": _ws_alerts.get(ws_id, [])}


@router.post("/{ws_id}/data-alerts")
def create_ws_alert(ws_id: int, data: WsAlertCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_ws_alert_id
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create alerts")
    alert = {
        "id": _next_ws_alert_id, "metric": data.metric,
        "threshold": data.threshold, "condition": data.condition,
        "notify_all": data.notify_all, "active": True,
        "created_by": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
        "triggered_count": 0,
    }
    _next_ws_alert_id += 1
    _ws_alerts[ws_id].append(alert)
    _log_activity(ws_id, user["sub"], "alert_created", f"{data.metric} {data.condition} {data.threshold}")
    return alert


@router.post("/{ws_id}/data-alerts/check")
def check_ws_alerts(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check current dataset against workspace alerts."""
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    from app.services.data_store import get as get_df
    df = get_df(user["sub"])
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
            _log_activity(ws_id, user["sub"], "alert_triggered", f"{col}={val:.2f} {cond} {thr}")
    return {"triggered": triggered, "checked": len(alerts)}


@router.delete("/{ws_id}/data-alerts/{alert_id}", status_code=204)
def delete_ws_alert(ws_id: int, alert_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    _ws_alerts[ws_id] = [a for a in _ws_alerts.get(ws_id, []) if a["id"] != alert_id]


# ── 20. AI Insights Feed ──────────────────────────────────────────────────────

@router.post("/{ws_id}/insights/generate")
def generate_insights(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Auto-generate insights from the user active dataset and share with workspace."""
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(user["sub"])
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
        insights.append("Dataset is complete — no missing values detected")
    # Save to workspace feed
    new_insights = []
    for text in insights:
        item = {
            "id": len(_insights.get(ws_id, [])) + len(new_insights) + 1,
            "text": text, "source": user["sub"],
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        new_insights.append(item)
    _insights[ws_id].extend(new_insights)
    if len(_insights[ws_id]) > 100:
        _insights[ws_id] = _insights[ws_id][-100:]
    _log_activity(ws_id, user["sub"], "insights_generated", f"{len(new_insights)} insights added")
    return {"insights": new_insights, "total_added": len(new_insights)}


@router.get("/{ws_id}/insights")
def get_insights(ws_id: int, limit: int = 30,
                 user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    items = list(reversed(_insights.get(ws_id, [])))[:limit]
    return {"insights": items, "total": len(_insights.get(ws_id, []))}


# ── 21. Member Leaderboard ────────────────────────────────────────────────────

@router.get("/{ws_id}/leaderboard")
def get_leaderboard(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
        entry["badge"] = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "⭐"
    return {"leaderboard": board, "your_rank": next((e["rank"] for e in board if e["email"] == user["sub"]), None)}


# ── 22. Workspace Webhooks ────────────────────────────────────────────────────

class WebhookCreate(BaseModel):
    url: str
    events: list = ["all"]   # all | chat_message | dataset_shared | task_created | alert_triggered
    secret: str = ""


@router.get("/{ws_id}/webhooks")
def list_webhooks(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can manage webhooks")
    hooks = _webhooks.get(ws_id, [])
    # Mask secret
    return {"webhooks": [{**h, "secret": "***" if h.get("secret") else ""} for h in hooks]}


@router.post("/{ws_id}/webhooks")
def create_webhook(ws_id: int, data: WebhookCreate,
                   user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_webhook_id
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can create webhooks")
    if not data.url.startswith("http"):
        raise HTTPException(400, "URL must start with http:// or https://")
    hook = {
        "id": _next_webhook_id, "url": data.url,
        "events": data.events, "secret": data.secret,
        "active": True, "created_by": user["sub"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "delivery_count": 0, "last_delivery": None,
    }
    _next_webhook_id += 1
    _webhooks[ws_id].append(hook)
    _log_activity(ws_id, user["sub"], "webhook_created", data.url[:50])
    return {**hook, "secret": "***" if hook["secret"] else ""}


@router.post("/{ws_id}/webhooks/{hook_id}/test")
async def test_webhook(ws_id: int, hook_id: int,
                       user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a test payload to the webhook URL."""
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can test webhooks")
    hook = next((h for h in _webhooks.get(ws_id, []) if h["id"] == hook_id), None)
    if not hook:
        raise HTTPException(404, "Webhook not found")
    payload = {"event": "test", "workspace_id": ws_id, "ts": datetime.now(timezone.utc).isoformat(), "triggered_by": user["sub"]}
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete webhooks")
    _webhooks[ws_id] = [h for h in _webhooks.get(ws_id, []) if h["id"] != hook_id]


# ── 23. Dataset Versioning ────────────────────────────────────────────────────

class VersionTag(BaseModel):
    tag: str = ""
    note: str = ""


@router.post("/{ws_id}/versions/snapshot")
def snapshot_dataset(ws_id: int, data: VersionTag,
                     user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save a versioned snapshot of the current dataset."""
    global _next_version_id
    role = _get_member_role(ws_id, user["sub"], db)
    if not role or role == "viewer":
        raise HTTPException(403, "Viewers cannot create snapshots")
    from app.services.data_store import get as get_df, save as save_df
    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset uploaded")
    version_name = f"v{_next_version_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    # Save as a named dataset in the workspace shared store
    _shared_datasets[ws_id][version_name] = {
        "name": version_name, "uploader": user["sub"],
        "rows": len(df), "cols": len(df.columns),
        "columns": list(df.columns),
        "ts": datetime.now(timezone.utc).isoformat(),
        "is_version": True,
    }
    version = {
        "id": _next_version_id, "name": version_name,
        "rows": len(df), "cols": len(df.columns),
        "tag": data.tag, "note": data.note,
        "saved_by": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_version_id += 1
    _versions[ws_id].append(version)
    _log_activity(ws_id, user["sub"], "version_snapshot", f"Snapshot '{version_name}' ({len(df)} rows)")
    return version


@router.get("/{ws_id}/versions")
def list_versions(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"versions": list(reversed(_versions.get(ws_id, [])))}


@router.post("/{ws_id}/versions/{version_id}/restore")
def restore_version(ws_id: int, version_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Restore a dataset version as the user active dataset."""
    role = _get_member_role(ws_id, user["sub"], db)
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
    save_df(user["sub"], uploader_df, version["name"])
    _log_activity(ws_id, user["sub"], "version_restored", f"Restored '{version['name']}'")
    return {"message": f"Version '{version['name']}' restored as your active dataset"}


# ── 24. Workspace Goals / KPI Targets ────────────────────────────────────────

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
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    goals = _goals.get(ws_id, [])
    # Auto-update current values from active dataset
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(user["sub"])
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create goals")
    goal = {
        "id": _next_goal_id, "title": data.title,
        "metric": data.metric, "target": data.target,
        "current": 0, "unit": data.unit, "deadline": data.deadline,
        "created_by": user["sub"], "ts": datetime.now(timezone.utc).isoformat(),
        "progress": 0,
    }
    _next_goal_id += 1
    _goals[ws_id].append(goal)
    _log_activity(ws_id, user["sub"], "goal_created", f"'{data.title}' target={data.target}{data.unit}")
    return goal


@router.patch("/{ws_id}/goals/{goal_id}")
def update_goal_progress(ws_id: int, goal_id: int, data: GoalUpdate,
                         user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    goal = next((g for g in _goals.get(ws_id, []) if g["id"] == goal_id), None)
    if not goal:
        raise HTTPException(404, "Goal not found")
    goal["current"] = data.current
    goal["progress"] = round(min(100, data.current / goal["target"] * 100), 1) if goal["target"] else 0
    goal["updated_by"] = user["sub"]
    _log_activity(ws_id, user["sub"], "goal_updated", f"'{goal['title']}' progress={goal['progress']}%")
    return goal


@router.delete("/{ws_id}/goals/{goal_id}", status_code=204)
def delete_goal(ws_id: int, goal_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete goals")
    _goals[ws_id] = [g for g in _goals.get(ws_id, []) if g["id"] != goal_id]

'''

with open(path, "a", encoding="utf-8") as f:
    f.write(BLOCK)

import ast
ast.parse(open(path, encoding="utf-8").read())
print("Syntax OK - lines:", len(open(path, encoding="utf-8").readlines()))
