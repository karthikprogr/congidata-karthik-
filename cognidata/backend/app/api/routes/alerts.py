"""KPI Threshold Alert routes - define rules, check live data, get alert history."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# In-memory per-user rules and history
_rules: dict[str, list[dict]] = {}
_history: dict[str, list[dict]] = {}
_next_id = 1


class AlertRule(BaseModel):
    metric: str
    condition: str = "gt"   # gt | lt | eq | gte | lte
    threshold: float
    message: str = ""
    notify_email: bool = False


@router.get("/rules")
def list_rules(user: dict = Depends(get_current_user)):
    return _rules.get(user["sub"], [])


@router.post("/rules", status_code=201)
def create_rule(rule: AlertRule, user: dict = Depends(get_current_user)):
    global _next_id
    uid = user["sub"]
    if uid not in _rules:
        _rules[uid] = []
    entry = {**rule.model_dump(), "id": _next_id, "active": True}
    _rules[uid].append(entry)
    _next_id += 1
    return entry


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    _rules[uid] = [r for r in _rules.get(uid, []) if r["id"] != rule_id]


@router.post("/check")
def check_metrics(data: dict, user: dict = Depends(get_current_user)):
    """Check a dict of metric values against user's rules. Returns triggered alerts."""
    from datetime import datetime, timezone
    uid = user["sub"]
    rules = _rules.get(uid, [])
    triggered = []
    for rule in rules:
        if not rule.get("active"):
            continue
        val = data.get(rule["metric"])
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue
        cond = rule["condition"]
        thr  = rule["threshold"]
        hit = (cond == "gt" and val > thr) or (cond == "lt" and val < thr) or \
              (cond == "eq" and val == thr) or (cond == "gte" and val >= thr) or \
              (cond == "lte" and val <= thr)
        if hit:
            alert = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "rule_id": rule["id"],
                "metric": rule["metric"],
                "value": val,
                "threshold": thr,
                "condition": cond,
                "message": rule["message"] or f"{rule['metric']} {cond} {thr} (got {val})",
                "level": "critical" if abs(val - thr) / max(abs(thr), 1) > 0.5 else "warning",
            }
            triggered.append(alert)
            if uid not in _history:
                _history[uid] = []
            _history[uid].append(alert)
            if len(_history[uid]) > 500:
                _history[uid] = _history[uid][-500:]
            # Email notification
            if rule.get("notify_email"):
                try:
                    from app.services.email_service import alert_admin
                    alert_admin(f"KPI Alert: {alert['message']}", f"<p>{alert['message']}</p><p>Value: {val} | Threshold: {thr}</p>")
                except Exception:
                    pass
            # Fire webhook/slack/email actions
            try:
                from app.api.routes.actions import fire_actions_for_alert
                fire_actions_for_alert(uid, alert)
            except Exception:
                pass
    return {"triggered": triggered, "count": len(triggered)}


@router.get("/history")
def alert_history(limit: int = 50, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    hist = list(reversed(_history.get(uid, [])))[:limit]
    return {"alerts": hist, "total": len(_history.get(uid, []))}


@router.delete("/history", status_code=204)
def clear_history(user: dict = Depends(get_current_user)):
    _history.pop(user["sub"], None)
