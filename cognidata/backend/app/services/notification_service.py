"""Notification service — per-user notifications."""
from datetime import datetime, timezone
from collections import defaultdict

_notifications: dict[str, list[dict]] = defaultdict(list)
_next_id = 1

def send(user_id: str, title: str, message: str, ntype: str = "info") -> dict:
    global _next_id
    n = {"id": _next_id, "title": title, "message": message,
         "type": ntype, "read": False,
         "ts": datetime.now(timezone.utc).isoformat()}
    _notifications[user_id].append(n)
    _next_id += 1
    return n

def get_all(user_id: str, limit: int = 50) -> list[dict]:
    return list(reversed(_notifications[user_id]))[:limit]

def mark_read(user_id: str) -> None:
    for n in _notifications[user_id]:
        n["read"] = True

def unread_count(user_id: str) -> int:
    return sum(1 for n in _notifications[user_id] if not n["read"])
