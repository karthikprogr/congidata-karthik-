"""
Per-user conversation memory — last N messages sent to LLM for context.
"""
from collections import defaultdict
from typing import Any

_history: dict[str, list[dict]] = defaultdict(list)
MAX_TURNS = 10  # keep last 10 exchanges (20 messages)


def add(user_id: str, role: str, content: Any) -> None:
    _history[user_id].append({"role": role, "content": str(content)})
    # Keep only last MAX_TURNS * 2 messages
    if len(_history[user_id]) > MAX_TURNS * 2:
        _history[user_id] = _history[user_id][-MAX_TURNS * 2:]


def get_context(user_id: str) -> list[dict]:
    """Returns recent messages formatted for OpenAI API."""
    return list(_history[user_id])


def clear(user_id: str) -> None:
    _history.pop(user_id, None)
