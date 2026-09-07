"""
Conversation memory — last 5 turns injected into every LLM prompt.
"""
from collections import defaultdict

_store: dict[str, list[dict]] = defaultdict(list)
MAX_TURNS = 5


def add(user_id: str, role: str, content: str) -> None:
    _store[user_id].append({"role": role, "content": content[:500]})
    if len(_store[user_id]) > MAX_TURNS * 2:
        _store[user_id] = _store[user_id][-MAX_TURNS * 2:]


def get(user_id: str) -> list[dict]:
    return list(_store[user_id])


def clear(user_id: str) -> None:
    _store.pop(user_id, None)


def format_context(user_id: str) -> str:
    turns = get(user_id)
    if not turns:
        return ""
    lines = [f"{t['role'].upper()}: {t['content']}" for t in turns]
    return "Previous conversation:\n" + "\n".join(lines)
