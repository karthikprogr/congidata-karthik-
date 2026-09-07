"""Agent trace service — records last 200 AI/ML invocations."""
from datetime import datetime, timezone

_traces: list[dict] = []
MAX = 200

def record(agent: str, input_summary: str, output_type: str, duration_ms: float, user_id: str = "") -> None:
    _traces.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "input": input_summary[:120],
        "output_type": output_type,
        "duration_ms": round(duration_ms, 1),
        "user": user_id,
    })
    if len(_traces) > MAX:
        _traces.pop(0)

def get_traces(limit: int = 20) -> list[dict]:
    return list(reversed(_traces))[:limit]
