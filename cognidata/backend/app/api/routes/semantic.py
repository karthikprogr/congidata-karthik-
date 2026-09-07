"""Semantic Metric Layer - define metrics in plain English, query them consistently."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user

router = APIRouter(prefix="/semantic", tags=["Semantic"])

# Per-user metric definitions
_metrics: dict[str, dict] = {}   # user_id - {metric_name: definition}
_lineage: dict[str, list] = {}   # user_id - [{action, metric, ts}]


class MetricDef(BaseModel):
    name: str
    description: str
    formula: str          # pandas expression e.g. "df['sales'].sum()"
    unit: str = ""
    category: str = "general"
    tags: str = ""


class MetricQuery(BaseModel):
    metric_name: str


@router.get("/metrics")
def list_metrics(user: dict = Depends(get_current_user)):
    return list(_metrics.get(user["email"], {}).values())


@router.post("/metrics", status_code=201)
def define_metric(m: MetricDef, user: dict = Depends(get_current_user)):
    uid = user["email"]
    if uid not in _metrics:
        _metrics[uid] = {}
    _metrics[uid][m.name] = m.model_dump()
    _log_lineage(uid, "defined", m.name)
    return _metrics[uid][m.name]


@router.delete("/metrics/{name}", status_code=204)
def delete_metric(name: str, user: dict = Depends(get_current_user)):
    uid = user["email"]
    _metrics.get(uid, {}).pop(name, None)
    _log_lineage(uid, "deleted", name)


@router.post("/metrics/{name}/compute")
def compute_metric(name: str, user: dict = Depends(get_current_user)):
    """Evaluate a metric formula against the user's current dataset."""
    uid = user["email"]
    defn = _metrics.get(uid, {}).get(name)
    if not defn:
        raise HTTPException(404, f"Metric '{name}' not defined")
    from app.services.data_store import get as get_df
    df = get_df(uid)
    if df is None:
        raise HTTPException(404, "No dataset loaded")
    try:
        import pandas as pd, numpy as np
        local = {"df": df, "pd": pd, "np": np}
        result = eval(defn["formula"], {"__builtins__": {}}, local)
        _log_lineage(uid, "computed", name)
        return {
            "metric": name,
            "value": float(result) if hasattr(result, "__float__") else str(result),
            "unit": defn.get("unit", ""),
            "formula": defn["formula"],
        }
    except Exception as e:
        raise HTTPException(422, f"Formula error: {e}")


@router.post("/metrics/compute-all")
def compute_all(user: dict = Depends(get_current_user)):
    """Compute all defined metrics at once."""
    uid = user["email"]
    metrics = _metrics.get(uid, {})
    if not metrics:
        return {"results": []}
    from app.services.data_store import get as get_df
    df = get_df(uid)
    if df is None:
        raise HTTPException(404, "No dataset loaded")
    import pandas as pd, numpy as np
    local = {"df": df, "pd": pd, "np": np}
    results = []
    for name, defn in metrics.items():
        try:
            val = eval(defn["formula"], {"__builtins__": {}}, local)
            results.append({"metric": name, "value": float(val) if hasattr(val, "__float__") else str(val),
                             "unit": defn.get("unit", ""), "status": "ok"})
        except Exception as e:
            results.append({"metric": name, "value": None, "status": "error", "error": str(e)})
    return {"results": results}


@router.get("/lineage")
def get_lineage(user: dict = Depends(get_current_user)):
    return {"lineage": list(reversed(_lineage.get(user["email"], [])))[:100]}


def _log_lineage(uid: str, action: str, metric: str):
    from datetime import datetime, timezone
    if uid not in _lineage:
        _lineage[uid] = []
    _lineage[uid].append({"ts": datetime.now(timezone.utc).isoformat(), "action": action, "metric": metric})
    if len(_lineage[uid]) > 500:
        _lineage[uid] = _lineage[uid][-500:]
