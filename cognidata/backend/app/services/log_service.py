from datetime import datetime, timezone
from typing import Any

_logs: list[dict] = []
_metrics: list[dict] = []
MAX = 1000

def log_event(user: str, action: str, detail: Any = None):
    _logs.append({"ts": datetime.now(timezone.utc).isoformat(), "user": user,
                  "action": action, "detail": detail})
    if len(_logs) > MAX: _logs.pop(0)

def get_logs(limit: int = 100) -> list[dict]:
    return list(reversed(_logs))[:limit]

def record_request(endpoint: str, method: str, duration_ms: float, status: int, user: str = ""):
    _metrics.append({"ts": datetime.now(timezone.utc).isoformat(), "endpoint": endpoint,
                     "method": method, "duration_ms": round(duration_ms, 1),
                     "status": status, "user": user})
    if len(_metrics) > MAX: _metrics.pop(0)

def get_metrics(limit: int = 200) -> list[dict]:
    return list(reversed(_metrics))[:limit]

def get_summary() -> dict:
    if not _metrics: return {"total": 0, "avg_ms": 0, "errors": 0, "error_rate": 0}
    total = len(_metrics)
    errors = sum(1 for m in _metrics if m["status"] >= 400)
    avg = sum(m["duration_ms"] for m in _metrics) / total
    return {"total": total, "avg_ms": round(avg, 1), "errors": errors,
            "error_rate": round(errors / total * 100, 1)}
