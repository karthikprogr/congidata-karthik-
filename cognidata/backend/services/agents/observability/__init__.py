"""Observability agent — dataset snapshots, drift detection, health scoring."""
import hashlib
from datetime import datetime, timezone
from typing import Optional

_snapshots: dict[str, list[dict]] = {}  # user_id → [snapshot, ...]


def take_snapshot(user_id: str, df) -> dict:
    """Record a dataset snapshot for drift tracking."""
    import numpy as np
    snap = {
        "version": f"v{len(_snapshots.get(user_id, [])) + 1}",
        "ts": datetime.now(timezone.utc).isoformat(),
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": int(df.isnull().sum().sum()),
        "missing_pct": round(df.isnull().mean().mean() * 100, 2),
        "hash": hashlib.md5(str(list(df.columns)).encode()).hexdigest()[:8],
    }
    # Numeric stats
    nums = df.select_dtypes(include=np.number)
    if not nums.empty:
        snap["numeric_means"] = nums.mean().round(4).to_dict()
        snap["numeric_stds"] = nums.std().round(4).to_dict()
    if user_id not in _snapshots:
        _snapshots[user_id] = []
    _snapshots[user_id].append(snap)
    # Keep last 20
    if len(_snapshots[user_id]) > 20:
        _snapshots[user_id] = _snapshots[user_id][-20:]
    return snap


def get_snapshots(user_id: str) -> list[dict]:
    return list(reversed(_snapshots.get(user_id, [])))


def compute_drift(user_id: str) -> Optional[dict]:
    """Compare latest two snapshots and return drift report."""
    snaps = _snapshots.get(user_id, [])
    if len(snaps) < 2:
        return None
    latest, prev = snaps[-1], snaps[-2]
    issues = []
    health = 100

    # Schema drift
    added = set(latest["column_names"]) - set(prev["column_names"])
    removed = set(prev["column_names"]) - set(latest["column_names"])
    if added:
        issues.append({"type": "schema", "severity": "warning", "message": f"New columns: {list(added)}"})
        health -= 10
    if removed:
        issues.append({"type": "schema", "severity": "error", "message": f"Removed columns: {list(removed)}"})
        health -= 20

    # Volume drift
    row_change_pct = abs(latest["rows"] - prev["rows"]) / max(prev["rows"], 1) * 100
    if row_change_pct > 20:
        issues.append({"type": "volume", "severity": "warning", "message": f"Row count changed {row_change_pct:.1f}%"})
        health -= 10

    # Null rate drift
    null_change = abs(latest["missing_pct"] - prev["missing_pct"])
    if null_change > 5:
        issues.append({"type": "null_rate", "severity": "warning", "message": f"Null rate changed {null_change:.1f}%"})
        health -= 10

    # Distribution drift (mean shift)
    if "numeric_means" in latest and "numeric_means" in prev:
        for col in latest["numeric_means"]:
            if col in prev["numeric_means"]:
                old_m = prev["numeric_means"][col]
                new_m = latest["numeric_means"][col]
                if old_m and abs(new_m - old_m) / max(abs(old_m), 1) > 0.3:
                    issues.append({"type": "distribution", "severity": "info",
                                   "message": f"Mean shift in '{col}': {old_m:.2f} → {new_m:.2f}"})
                    health -= 5

    return {
        "health_score": max(0, health),
        "issues": issues,
        "latest": latest["version"],
        "previous": prev["version"],
        "row_change": latest["rows"] - prev["rows"],
        "col_change": latest["columns"] - prev["columns"],
    }


def clear_snapshots(user_id: str) -> None:
    _snapshots.pop(user_id, None)
