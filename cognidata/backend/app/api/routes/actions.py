"""
Option B/C - Action Layer
Webhook triggers, Slack notifications, auto-actions on alert fire.
"""
import httpx, asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user

router = APIRouter(prefix="/actions", tags=["Actions"])

# In-memory action store per user
_actions: dict[str, list[dict]] = {}
_action_logs: dict[str, list[dict]] = {}
_next_id = 1


class ActionCreate(BaseModel):
    name: str
    trigger: str = "alert"          # alert | schedule | manual
    type: str = "webhook"           # webhook | slack | email | pipeline
    url: Optional[str] = None       # for webhook / slack
    payload_template: Optional[str] = None
    pipeline_id: Optional[int] = None
    rule_id: Optional[int] = None   # bind to specific alert rule
    active: bool = True


# - CRUD -

@router.get("")
def list_actions(user: dict = Depends(get_current_user)):
    return _actions.get(user["sub"], [])


@router.post("", status_code=201)
def create_action(data: ActionCreate, user: dict = Depends(get_current_user)):
    global _next_id
    uid = user["sub"]
    if uid not in _actions:
        _actions[uid] = []
    entry = {**data.model_dump(), "id": _next_id,
             "created_at": datetime.now(timezone.utc).isoformat()}
    _actions[uid].append(entry)
    _next_id += 1
    return entry


@router.get("/logs")
def action_logs(limit: int = 50, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    return _action_logs.get(uid, [])[:limit]


@router.delete("/logs", status_code=204)
def clear_logs(user: dict = Depends(get_current_user)):
    _action_logs.pop(user["sub"], None)


@router.patch("/{action_id}")
def update_action(action_id: int, data: dict, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    for a in _actions.get(uid, []):
        if a["id"] == action_id:
            a.update({k: v for k, v in data.items() if k != "id"})
            return a
    raise HTTPException(404, "Action not found")


@router.delete("/{action_id}", status_code=204)
def delete_action(action_id: int, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    _actions[uid] = [a for a in _actions.get(uid, []) if a["id"] != action_id]


# - Manual trigger -

@router.post("/{action_id}/run")
async def run_action(action_id: int, context: dict = {},
                     user: dict = Depends(get_current_user),
                     bg: BackgroundTasks = None):
    uid = user["sub"]
    action = next((a for a in _actions.get(uid, []) if a["id"] == action_id), None)
    if not action:
        raise HTTPException(404, "Action not found")
    result = await _execute_action(action, context, uid)
    return result


async def _execute_action(action: dict, context: dict, uid: str) -> dict:
    """Execute a single action and log the result."""
    ts = datetime.now(timezone.utc).isoformat()
    log_entry = {"action_id": action["id"], "name": action["name"],
                 "type": action["type"], "ts": ts, "context": context}
    try:
        if action["type"] == "webhook":
            result = await _fire_webhook(action, context)
        elif action["type"] == "slack":
            result = await _fire_slack(action, context)
        elif action["type"] == "email":
            result = _fire_email(action, context, uid)
        else:
            result = {"status": "skipped", "reason": f"Unknown type: {action['type']}"}

        log_entry["result"] = result
        log_entry["success"] = result.get("status") == "ok"
    except Exception as e:
        log_entry["result"] = {"status": "error", "error": str(e)}
        log_entry["success"] = False

    if uid not in _action_logs:
        _action_logs[uid] = []
    _action_logs[uid].insert(0, log_entry)
    if len(_action_logs[uid]) > 200:
        _action_logs[uid] = _action_logs[uid][:200]
    return log_entry


async def _fire_webhook(action: dict, context: dict) -> dict:
    url = action.get("url")
    if not url:
        return {"status": "error", "error": "No URL configured"}
    payload = {"source": "cognidata", "action": action["name"],
               "timestamp": datetime.now(timezone.utc).isoformat(), **context}
    if action.get("payload_template"):
        try:
            import json
            tpl = action["payload_template"]
            for k, v in context.items():
                tpl = tpl.replace(f"{{{k}}}", str(v))
            payload = json.loads(tpl)
        except Exception:
            pass
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload)
        return {"status": "ok", "http_status": r.status_code, "response": r.text[:200]}


async def _fire_slack(action: dict, context: dict) -> dict:
    url = action.get("url")
    if not url:
        return {"status": "error", "error": "No Slack webhook URL configured"}
    metric = context.get("metric", "metric")
    value = context.get("value", "")
    threshold = context.get("threshold", "")
    message = context.get("message", f"Alert: {metric} = {value} (threshold: {threshold})")
    payload = {
        "text": f"- *COGNIDATA Alert*\n{message}",
        "attachments": [{
            "color": "#ef4444",
            "fields": [
                {"title": "Metric", "value": str(metric), "short": True},
                {"title": "Value", "value": str(value), "short": True},
                {"title": "Threshold", "value": str(threshold), "short": True},
                {"title": "Time", "value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "short": True},
            ]
        }]
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload)
        return {"status": "ok", "http_status": r.status_code}


def _fire_email(action: dict, context: dict, uid: str) -> dict:
    try:
        from app.services.email_service import send_async, _html_wrap, _info_row
        metric = context.get("metric", "")
        value = context.get("value", "")
        message = context.get("message", f"Alert triggered: {metric} = {value}")
        body = _html_wrap("Action Triggered", f"""
        <p style="color:#e4e4e7;font-size:15px;margin:0 0 20px">{message}</p>
        <table style="width:100%;border-collapse:collapse">
          {_info_row("Action", action['name'])}
          {_info_row("Metric", str(metric))}
          {_info_row("Value", str(value))}
          {_info_row("Time", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))}
        </table>""")
        from app.core.config import ADMIN_EMAIL
        to = ADMIN_EMAIL or uid
        send_async(to, f"COGNIDATA Action: {action['name']}", body)
        return {"status": "ok", "sent_to": to}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# - Called internally by alerts when a rule fires -

def fire_actions_for_alert(uid: str, alert: dict):
    """Called by alerts route when a rule fires. Runs matching actions in a background thread."""
    rule_id = alert.get("rule_id")
    matching = [
        a for a in _actions.get(uid, [])
        if a.get("active") and a.get("trigger") == "alert"
        and (a.get("rule_id") is None or a.get("rule_id") == rule_id)
    ]
    if not matching:
        return

    import threading

    def _run_in_thread():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_all_with_retry(matching, alert, uid))
        finally:
            loop.close()

    t = threading.Thread(target=_run_in_thread, daemon=True)
    t.start()


async def _run_all_with_retry(actions: list, context: dict, uid: str):
    """Execute all actions with retry logic (up to 3 attempts, exponential backoff)."""
    import asyncio
    for action in actions:
        for attempt in range(3):
            try:
                result = await _execute_action(action, context, uid)
                if result.get("success"):
                    break
                # Non-success but no exception - don't retry
                break
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)   # 1s, 2s backoff
                else:
                    # Final attempt failed - log it
                    ts = datetime.now(timezone.utc).isoformat()
                    if uid not in _action_logs:
                        _action_logs[uid] = []
                    _action_logs[uid].insert(0, {
                        "action_id": action["id"], "name": action["name"],
                        "type": action["type"], "ts": ts, "context": context,
                        "result": {"status": "error", "error": str(e), "attempts": 3},
                        "success": False,
                    })
