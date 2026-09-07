"""API key management — aida_ prefix, validation, revocation."""
import secrets
from datetime import datetime, timezone

_keys: dict[str, dict] = {}  # key → {user_id, name, created, last_used, active}

def generate(user_id: str, name: str = "default") -> dict:
    key = "aida_" + secrets.token_urlsafe(32)
    entry = {"key": key, "user_id": user_id, "name": name,
             "created": datetime.now(timezone.utc).isoformat(),
             "last_used": None, "active": True}
    _keys[key] = entry
    return entry

def validate(key: str) -> dict | None:
    entry = _keys.get(key)
    if entry and entry["active"]:
        entry["last_used"] = datetime.now(timezone.utc).isoformat()
        return entry
    return None

def revoke(key: str, user_id: str) -> bool:
    entry = _keys.get(key)
    if entry and entry["user_id"] == user_id:
        entry["active"] = False
        return True
    return False

def list_keys(user_id: str) -> list[dict]:
    return [{"key": k[:12]+"...", "name": v["name"], "created": v["created"],
             "last_used": v["last_used"], "active": v["active"]}
            for k, v in _keys.items() if v["user_id"] == user_id]
