"""Feedback service — submit, retrieve, rate."""
from datetime import datetime, timezone
from typing import Any

_feedback: list[dict] = []
_next_id = 1

def submit(user_id: str, message: str, rating: int = 5, category: str = "general") -> dict:
    global _next_id
    entry = {"id": _next_id, "user": user_id, "message": message,
             "rating": max(1, min(5, rating)), "category": category,
             "ts": datetime.now(timezone.utc).isoformat()}
    _feedback.append(entry)
    _next_id += 1
    return entry

def get_all(limit: int = 100) -> list[dict]:
    return list(reversed(_feedback))[:limit]

def get_avg_rating() -> float:
    if not _feedback: return 0.0
    return round(sum(f["rating"] for f in _feedback) / len(_feedback), 2)

def get_stats() -> dict:
    if not _feedback: return {"total": 0, "avg_rating": 0, "by_category": {}}
    by_cat = {}
    for f in _feedback:
        by_cat[f["category"]] = by_cat.get(f["category"], 0) + 1
    return {"total": len(_feedback), "avg_rating": get_avg_rating(), "by_category": by_cat}
