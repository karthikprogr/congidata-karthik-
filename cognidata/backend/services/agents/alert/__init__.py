"""Alert agent — threshold-based alerting on geo/metric data."""
from datetime import datetime, timezone

_alerts: list[dict] = []
_rules: list[dict] = []  # {metric, threshold, condition, message}
_next_id = 1


def add_rule(metric: str, threshold: float, condition: str = "gt", message: str = "") -> dict:
    global _next_id
    rule = {"id": _next_id, "metric": metric, "threshold": threshold,
            "condition": condition, "message": message, "active": True}
    _rules.append(rule)
    _next_id += 1
    return rule


def check(data: dict) -> list[dict]:
    """Check data dict against all active rules. Returns triggered alerts."""
    triggered = []
    for rule in _rules:
        if not rule["active"]:
            continue
        val = data.get(rule["metric"])
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue
        hit = False
        if rule["condition"] == "gt" and val > rule["threshold"]:
            hit = True
        elif rule["condition"] == "lt" and val < rule["threshold"]:
            hit = True
        elif rule["condition"] == "eq" and val == rule["threshold"]:
            hit = True
        if hit:
            alert = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "metric": rule["metric"],
                "value": val,
                "threshold": rule["threshold"],
                "condition": rule["condition"],
                "message": rule["message"] or f"{rule['metric']} {rule['condition']} {rule['threshold']} (got {val})",
                "level": "critical" if abs(val - rule["threshold"]) / max(abs(rule["threshold"]), 1) > 0.5 else "warning",
            }
            _alerts.append(alert)
            triggered.append(alert)
    # Keep last 200
    if len(_alerts) > 200:
        _alerts[:] = _alerts[-200:]
    return triggered


def get_alerts(limit: int = 50) -> list[dict]:
    return list(reversed(_alerts))[:limit]


def get_rules() -> list[dict]:
    return list(_rules)


def clear_alerts() -> None:
    _alerts.clear()
