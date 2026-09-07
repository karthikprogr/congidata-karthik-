"""SQL Agent routes - NL-pandas with auto-fix."""
import sys, pathlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user, get_api_key
from app.services.data_store import get as get_df

router = APIRouter(prefix="/sql", tags=["SQL Agent"])

def _boot():
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)

class SQLQuery(BaseModel):
    question: str

@router.post("/query")
def sql_query(req: SQLQuery, api_key: str = Depends(get_api_key),
              user: dict = Depends(get_current_user)):
    _boot()
    from agents.sql.sql_agent import run_sql_agent
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found")
    result = run_sql_agent(req.question, df, api_key)
    if result.get("error") and result.get("result") is None:
        raise HTTPException(422, result["error"])

    import pandas as pd
    r = result.get("result")
    if isinstance(r, pd.DataFrame):
        data = r.replace({float("nan"): None}).to_dict("records")
        rtype = "table"
    elif isinstance(r, pd.Series):
        data = r.where(r.notna(), None).to_dict()
        rtype = "json"
    else:
        data = str(r) if r is not None else None
        rtype = "text"

    return {"type": rtype, "data": data, "code": result.get("code"), "task_type": "sql"}
