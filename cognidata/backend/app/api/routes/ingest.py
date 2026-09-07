"""
Option C - Real-Time Data Ingestion
Webhook endpoint to stream data into live datasets.
POST /api/ingest/:stream_id  - append rows in real-time
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user

router = APIRouter(prefix="/ingest", tags=["Ingest"])

# stream_id -> {owner, name, schema, rows, created_at, api_key}
_streams: dict[str, dict] = {}
# api_key -> stream_id (for keyless auth on ingest endpoint)
_stream_keys: dict[str, str] = {}


class StreamCreate(BaseModel):
    name: str
    description: str = ""
    max_rows: int = 10000   # rolling window


class StreamRow(BaseModel):
    data: dict
    ts: Optional[str] = None


# - Stream management -

@router.get("/streams")
def list_streams(user: dict = Depends(get_current_user)):
    return [
        {**v, "stream_id": k, "row_count": len(v.get("rows", []))}
        for k, v in _streams.items()
        if v.get("owner") == user["email"]
    ]


@router.post("/streams", status_code=201)
def create_stream(data: StreamCreate, user: dict = Depends(get_current_user)):
    stream_id = str(uuid.uuid4())[:12]
    api_key = str(uuid.uuid4()).replace("-", "")
    _streams[stream_id] = {
        "owner": user["email"],
        "name": data.name,
        "description": data.description,
        "max_rows": data.max_rows,
        "rows": [],
        "schema": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "api_key": api_key,
    }
    _stream_keys[api_key] = stream_id
    return {"stream_id": stream_id, "api_key": api_key,
            "endpoint": f"/api/ingest/{stream_id}",
            "message": f"Stream '{data.name}' created. POST JSON rows to the endpoint."}


@router.delete("/streams/{stream_id}", status_code=204)
def delete_stream(stream_id: str, user: dict = Depends(get_current_user)):
    s = _streams.get(stream_id)
    if not s:
        raise HTTPException(404, "Stream not found")
    if s["owner"] != user["email"]:
        raise HTTPException(403, "Not your stream")
    key = s.get("api_key")
    if key:
        _stream_keys.pop(key, None)
    del _streams[stream_id]


@router.get("/streams/{stream_id}")
def get_stream(stream_id: str, user: dict = Depends(get_current_user)):
    s = _streams.get(stream_id)
    if not s:
        raise HTTPException(404, "Stream not found")
    if s["owner"] != user["email"]:
        raise HTTPException(403, "Not your stream")
    return {**s, "stream_id": stream_id, "row_count": len(s["rows"]),
            "recent": s["rows"][-20:]}


@router.delete("/streams/{stream_id}/rows", status_code=204)
def clear_stream(stream_id: str, user: dict = Depends(get_current_user)):
    s = _streams.get(stream_id)
    if not s or s["owner"] != user["email"]:
        raise HTTPException(404, "Stream not found")
    s["rows"] = []


# - Ingest endpoint (API-key auth, no JWT needed) -

@router.post("/{stream_id}")
async def ingest_row(stream_id: str, request: Request):
    """
    Append one or more rows to a stream.
    Auth: pass stream API key as header X-Stream-Key or query param key=
    Body: JSON object (single row) or array of objects (batch)
    """
    # Auth
    key = request.headers.get("x-stream-key") or request.query_params.get("key", "")
    s = _streams.get(stream_id)
    if not s:
        raise HTTPException(404, "Stream not found")
    if s.get("api_key") and s["api_key"] != key:
        raise HTTPException(401, "Invalid stream key")

    body = await request.json()
    rows = body if isinstance(body, list) else [body]
    ts = datetime.now(timezone.utc).isoformat()

    appended = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        row["_ts"] = row.get("_ts") or ts
        s["rows"].append(row)
        appended += 1
        # Update schema
        for k, v in row.items():
            if k not in s["schema"]:
                s["schema"][k] = type(v).__name__

    # Rolling window
    max_rows = s.get("max_rows", 10000)
    if len(s["rows"]) > max_rows:
        s["rows"] = s["rows"][-max_rows:]

    # Auto-check alerts if owner has rules
    try:
        from app.api.routes.alerts import _rules, _history
        from app.api.routes.actions import fire_actions_for_alert
        uid = s["owner"]
        rules = _rules.get(uid, [])
        if rules and rows:
            last = rows[-1]
            for rule in rules:
                if not rule.get("active"):
                    continue
                val = last.get(rule["metric"])
                if val is None:
                    continue
                try:
                    val = float(val)
                except Exception:
                    continue
                cond, thr = rule["condition"], rule["threshold"]
                hit = (cond == "gt" and val > thr) or (cond == "lt" and val < thr) or \
                      (cond == "eq" and val == thr) or (cond == "gte" and val >= thr) or \
                      (cond == "lte" and val <= thr)
                if hit:
                    alert = {"ts": ts, "rule_id": rule["id"], "metric": rule["metric"],
                             "value": val, "threshold": thr, "condition": cond,
                             "message": rule["message"] or f"{rule['metric']} {cond} {thr}",
                             "level": "critical" if abs(val - thr) / max(abs(thr), 1) > 0.5 else "warning",
                             "stream_id": stream_id}
                    if uid not in _history:
                        _history[uid] = []
                    _history[uid].append(alert)
                    fire_actions_for_alert(uid, alert)
    except Exception:
        pass

    return {"appended": appended, "total": len(s["rows"]), "stream_id": stream_id}


# - Load stream into dataset for analysis -

@router.post("/streams/{stream_id}/load")
def load_stream_as_dataset(stream_id: str, user: dict = Depends(get_current_user)):
    """Load stream rows into the user's active dataset for AI analysis."""
    s = _streams.get(stream_id)
    if not s or s["owner"] != user["email"]:
        raise HTTPException(404, "Stream not found")
    if not s["rows"]:
        raise HTTPException(400, "Stream is empty")
    import pandas as pd
    from app.services.data_store import save as save_df
    df = pd.DataFrame(s["rows"])
    save_df(user["email"], df)
    return {"message": f"Loaded {len(df)} rows from stream '{s['name']}' as active dataset",
            "rows": len(df), "columns": list(df.columns)}
