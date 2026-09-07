"""AI Data Catalog & Lineage - auto-document columns, track usage, quality scores."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user, get_api_key

router = APIRouter(prefix="/catalog", tags=["Catalog"])

_catalogs: dict[str, dict] = {}   # user_id - {col_name: metadata}
_lineage_log: dict[str, list] = {}


class ColumnAnnotation(BaseModel):
    column: str
    description: str = ""
    tags: str = ""
    owner: str = ""
    pii: bool = False


@router.get("/columns")
def get_catalog(user: dict = Depends(get_current_user)):
    """Get the data catalog for the current dataset."""
    uid = user["sub"]
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(uid)
    if df is None:
        raise HTTPException(404, "No dataset loaded")

    catalog = _catalogs.get(uid, {})
    result = []
    for col in df.columns:
        meta = catalog.get(col, {})
        nulls = int(df[col].isnull().sum())
        total = len(df)
        completeness = round((1 - nulls / total) * 100, 1) if total > 0 else 0
        unique = int(df[col].nunique())
        quality = _quality_score(completeness, unique, total)
        entry = {
            "column": col,
            "dtype": str(df[col].dtype),
            "nulls": nulls,
            "null_pct": round(nulls / total * 100, 1) if total > 0 else 0,
            "unique": unique,
            "completeness": completeness,
            "quality_score": quality,
            "description": meta.get("description", ""),
            "tags": meta.get("tags", ""),
            "owner": meta.get("owner", ""),
            "pii": meta.get("pii", False),
        }
        if df[col].dtype != object:
            entry["mean"] = round(float(df[col].mean()), 3) if not df[col].isnull().all() else None
            entry["std"]  = round(float(df[col].std()), 3) if not df[col].isnull().all() else None
        else:
            top = df[col].value_counts().head(3).to_dict()
            entry["top_values"] = {str(k): int(v) for k, v in top.items()}
        result.append(entry)
    return result


@router.post("/columns/annotate")
def annotate_column(ann: ColumnAnnotation, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    if uid not in _catalogs:
        _catalogs[uid] = {}
    _catalogs[uid][ann.column] = ann.model_dump()
    _log(uid, "annotated", ann.column)
    return {"message": f"Column '{ann.column}' annotated"}


@router.post("/auto-document")
def auto_document(api_key: str = Depends(get_api_key), user: dict = Depends(get_current_user)):
    """Use LLM to auto-generate descriptions for all columns."""
    import os
    from app.services.data_store import get as get_df
    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset loaded")

    uid = user["sub"]
    if uid not in _catalogs:
        _catalogs[uid] = {}

    try:
        from openai import OpenAI
        import json, re
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        client = OpenAI(api_key=key)

        col_info = []
        for col in df.columns[:20]:
            sample = df[col].dropna().head(3).tolist()
            col_info.append(f"{col} ({df[col].dtype}): sample={sample}")

        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content":
                f"Dataset columns:\n{chr(10).join(col_info)}\n\n"
                "Generate a JSON object where keys are column names and values are short descriptions (1 sentence each).\n"
                "Return ONLY the JSON object."}],
            temperature=0.2, max_tokens=600,
        )
        content = re.sub(r"```(?:json)?|```", "", resp.choices[0].message.content.strip()).strip()
        descriptions = json.loads(content)
        for col, desc in descriptions.items():
            if col not in _catalogs[uid]:
                _catalogs[uid][col] = {}
            _catalogs[uid][col]["description"] = desc
        _log(uid, "auto-documented", "all columns")
        return {"documented": len(descriptions), "descriptions": descriptions}
    except Exception as e:
        # Fallback: rule-based descriptions
        descriptions = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if "int" in dtype or "float" in dtype:
                descriptions[col] = f"Numeric column - {col.replace('_', ' ')}"
            elif "object" in dtype:
                descriptions[col] = f"Categorical column - {col.replace('_', ' ')}"
            elif "date" in dtype or "time" in dtype:
                descriptions[col] = f"Date/time column - {col.replace('_', ' ')}"
            else:
                descriptions[col] = f"Column: {col}"
            if col not in _catalogs[uid]:
                _catalogs[uid][col] = {}
            _catalogs[uid][col]["description"] = descriptions[col]
        return {"documented": len(descriptions), "descriptions": descriptions, "method": "rule-based"}


@router.get("/lineage")
def get_lineage(user: dict = Depends(get_current_user)):
    return {"lineage": list(reversed(_lineage_log.get(user["sub"], [])))[:100]}


def _quality_score(completeness: float, unique: int, total: int) -> int:
    score = completeness
    if unique == 1:
        score -= 20  # constant column
    if unique == total and total > 10:
        score -= 10  # all unique (likely ID)
    return max(0, min(100, round(score)))


def _log(uid: str, action: str, target: str):
    from datetime import datetime, timezone
    if uid not in _lineage_log:
        _lineage_log[uid] = []
    _lineage_log[uid].append({"ts": datetime.now(timezone.utc).isoformat(), "action": action, "target": target})
    if len(_lineage_log[uid]) > 500:
        _lineage_log[uid] = _lineage_log[uid][-500:]
