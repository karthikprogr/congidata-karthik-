import pathlib, ast

WS = pathlib.Path(r"D:\cogni-2-main\cognidata\backend\app\api\routes\workspaces.py")

BLOCK = """

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
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    polls = list(_polls.get(ws_id, {}).values())
    for p in polls:
        p["total_votes"] = sum(len(v) for v in p["votes"].values())
        p["user_voted"] = any(user["sub"] in v for v in p["votes"].values())
    return {"polls": polls}


@router.post("/{ws_id}/polls")
def create_poll(ws_id: int, data: PollCreate,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_poll_id
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create polls")
    poll = {
        "id": _next_poll_id, "question": data.question,
        "options": data.options,
        "votes": {opt: [] for opt in data.options},
        "created_by": user["sub"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "closed": False,
    }
    _next_poll_id += 1
    if ws_id not in _polls:
        _polls[ws_id] = {}
    _polls[ws_id][poll["id"]] = poll
    _log_activity(ws_id, user["sub"], "poll_created", f"'{data.question}'")
    return poll


@router.post("/{ws_id}/polls/{poll_id}/vote")
def vote_poll(ws_id: int, poll_id: int, data: PollVote,
              user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
        if user["sub"] in opt_voters:
            opt_voters.remove(user["sub"])
    poll["votes"][data.option].append(user["sub"])
    _log_activity(ws_id, user["sub"], "poll_voted", f"Voted '{data.option}'")
    return {"votes": poll["votes"], "total": sum(len(v) for v in poll["votes"].values())}


@router.post("/{ws_id}/polls/{poll_id}/close")
def close_poll(ws_id: int, poll_id: int,
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can close polls")
    poll = _polls.get(ws_id, {}).get(poll_id)
    if not poll:
        raise HTTPException(404, "Poll not found")
    poll["closed"] = True
    winner = max(poll["votes"], key=lambda k: len(poll["votes"][k])) if poll["votes"] else None
    _log_activity(ws_id, user["sub"], "poll_closed", f"Winner: '{winner}'")
    return {"message": "Poll closed", "winner": winner}


@router.delete("/{ws_id}/polls/{poll_id}", status_code=204)
def delete_poll(ws_id: int, poll_id: int,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"contracts": list(_contracts.get(ws_id, {}).values())}


@router.post("/{ws_id}/contracts")
def create_contract(ws_id: int, data: ContractCreate,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_contract_id
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot create contracts")
    contract = {
        "id": _next_contract_id, "name": data.name,
        "description": data.description, "schema_def": data.schema_def,
        "sla": data.sla, "owner": user["sub"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "active", "violations": [],
    }
    _next_contract_id += 1
    if ws_id not in _contracts:
        _contracts[ws_id] = {}
    _contracts[ws_id][contract["id"]] = contract
    _log_activity(ws_id, user["sub"], "contract_created", f"'{data.name}'")
    return contract


@router.post("/{ws_id}/contracts/{contract_id}/validate")
def validate_contract(ws_id: int, contract_id: int,
                      user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    contract = _contracts.get(ws_id, {}).get(contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    from app.services.data_store import get as get_df
    df = get_df(user["sub"])
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
    _log_activity(ws_id, user["sub"], "contract_validated",
                  f"'{contract['name']}': {'valid' if not violations else str(len(violations)) + ' violations'}")
    return {"valid": not violations, "violations": violations}


@router.delete("/{ws_id}/contracts/{contract_id}", status_code=204)
def delete_contract(ws_id: int, contract_id: int,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can add integrations")
    if data.type not in ("slack", "teams", "discord", "email", "custom"):
        raise HTTPException(400, "Invalid integration type")
    intg = {
        "id": _next_integration_id, "type": data.type,
        "name": data.name or data.type.title(),
        "webhook_url": data.webhook_url, "events": data.events,
        "config": data.config, "active": True,
        "created_by": user["sub"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "deliveries": 0,
    }
    _next_integration_id += 1
    if ws_id not in _integrations:
        _integrations[ws_id] = {}
    _integrations[ws_id][intg["id"]] = intg
    _log_activity(ws_id, user["sub"], "integration_added", f"{data.type}: {data.name}")
    return {**intg, "webhook_url": intg["webhook_url"][:30] + "***" if intg["webhook_url"] else ""}


@router.post("/{ws_id}/integrations/{intg_id}/test")
async def test_integration(ws_id: int, intg_id: int,
                           user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can update permissions")
    if ws_id not in _permissions:
        _permissions[ws_id] = {}
    if data.user_email not in _permissions[ws_id]:
        _permissions[ws_id][data.user_email] = {}
    _permissions[ws_id][data.user_email].update(data.permissions)
    _log_activity(ws_id, user["sub"], "permissions_updated",
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
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"changelog": list(reversed(_changelog.get(ws_id, [])))}


@router.post("/{ws_id}/changelog")
def add_changelog(ws_id: int, data: ChangelogEntry,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_changelog_id
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot add changelog entries")
    entry = {
        "id": _next_changelog_id, "version": data.version,
        "title": data.title, "body": data.body,
        "breaking": data.breaking, "author": user["sub"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _next_changelog_id += 1
    if ws_id not in _changelog:
        _changelog[ws_id] = []
    _changelog[ws_id].append(entry)
    _log_activity(ws_id, user["sub"], "changelog_added",
                  f"v{data.version}: {data.title}")
    return entry


@router.delete("/{ws_id}/changelog/{entry_id}", status_code=204)
def delete_changelog(ws_id: int, entry_id: int,
                     user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    return {"metrics": list(_metrics_board.get(ws_id, {}).values())}


@router.post("/{ws_id}/metrics")
def add_metric(ws_id: int, data: MetricCreate,
               user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _next_metric_id
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin", "editor"):
        raise HTTPException(403, "Viewers cannot add metrics")
    metric = {
        "id": _next_metric_id, "name": data.name,
        "value": data.value, "unit": data.unit, "trend": data.trend,
        "updated_by": user["sub"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "history": [{"value": data.value, "ts": datetime.now(timezone.utc).isoformat()}],
    }
    _next_metric_id += 1
    if ws_id not in _metrics_board:
        _metrics_board[ws_id] = {}
    _metrics_board[ws_id][metric["id"]] = metric
    _log_activity(ws_id, user["sub"], "metric_added", f"'{data.name}' = {data.value}{data.unit}")
    return metric


@router.patch("/{ws_id}/metrics/{metric_id}")
def update_metric(ws_id: int, metric_id: int, data: MetricCreate,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if not role:
        raise HTTPException(403, "Not a member")
    metric = _metrics_board.get(ws_id, {}).get(metric_id)
    if not metric:
        raise HTTPException(404, "Metric not found")
    old_val = metric["value"]
    metric["value"] = data.value
    metric["trend"] = "up" if data.value > old_val else "down" if data.value < old_val else "stable"
    metric["updated_by"] = user["sub"]
    metric["ts"] = datetime.now(timezone.utc).isoformat()
    metric["history"].append({"value": data.value, "ts": metric["ts"]})
    if len(metric["history"]) > 30:
        metric["history"] = metric["history"][-30:]
    return metric


@router.delete("/{ws_id}/metrics/{metric_id}", status_code=204)
def delete_metric(ws_id: int, metric_id: int,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can delete metrics")
    if metric_id in _metrics_board.get(ws_id, {}):
        del _metrics_board[ws_id][metric_id]


# 31. Workspace Backup & Restore
import json as _json_mod

@router.get("/{ws_id}/backup")
def backup_workspace(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can backup workspace")
    ws = db.query(Workspace).filter(Workspace.id == ws_id).first()
    backup = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": user["sub"],
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
    _log_activity(ws_id, user["sub"], "workspace_backup", "Full backup exported")
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
    role = _get_member_role(ws_id, user["sub"], db)
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
    _log_activity(ws_id, user["sub"], "workspace_restored", f"Restored: {', '.join(restored)}")
    return {"message": "Workspace restored", "restored": restored}


# 32. Workspace Digest (AI-powered weekly summary)
@router.get("/{ws_id}/digest")
def get_digest(ws_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = _get_member_role(ws_id, user["sub"], db)
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

"""

with open(WS, "a", encoding="utf-8") as f:
    f.write(BLOCK)

ast.parse(open(WS, encoding="utf-8").read())
print("Syntax OK - lines:", len(open(WS, encoding="utf-8").readlines()))
