"""Reports routes - PDF generation, data profiling, export."""
import sys, pathlib, io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user, get_api_key
from app.services.data_store import get as get_df

router = APIRouter(prefix="/reports", tags=["Reports"])

def _boot():
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)

class PDFRequest(BaseModel):
    title: str = "COGNIDATA Report"
    include_insights: bool = True

@router.post("/pdf")
async def generate_pdf(req: PDFRequest, api_key: str = Depends(get_api_key),
                       user: dict = Depends(get_current_user)):
    _boot()
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found")

    insights = ""
    if req.include_insights:
        try:
            from agents.llm_agent import run_insight
            insights = run_insight(df, api_key)
        except Exception:
            pass

    from agents.reports.pdf_generator import generate_pdf as _gen
    pdf_bytes = _gen(df, title=req.title, insights=insights)
    return StreamingResponse(io.BytesIO(pdf_bytes),
                             media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{req.title}.pdf"'})

@router.get("/profile")
def profile(user: dict = Depends(get_current_user)):
    """Per-column data profiling."""
    import numpy as np
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found")
    result = []
    for col in df.columns:
        info = {
            "column": col,
            "dtype": str(df[col].dtype),
            "nulls": int(df[col].isnull().sum()),
            "null_pct": round(df[col].isnull().mean() * 100, 1),
            "unique": int(df[col].nunique()),
            "completeness": round((1 - df[col].isnull().mean()) * 100, 1),
        }
        if df[col].dtype != object:
            info.update({
                "mean": round(float(df[col].mean()), 3) if not df[col].isnull().all() else None,
                "std":  round(float(df[col].std()), 3) if not df[col].isnull().all() else None,
                "min":  float(df[col].min()) if not df[col].isnull().all() else None,
                "max":  float(df[col].max()) if not df[col].isnull().all() else None,
            })
        else:
            info["top_values"] = df[col].value_counts().head(5).to_dict()
        result.append(info)
    return result

@router.get("/export/csv")
def export_csv(user: dict = Depends(get_current_user)):
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found")
    return StreamingResponse(io.StringIO(df.to_csv(index=False)),
                             media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=data.csv"})

@router.get("/export/json")
def export_json(user: dict = Depends(get_current_user)):
    import numpy as np
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found")
    return df.replace({float("nan"): None}).to_dict("records")


@router.get("/export/excel")
def export_excel(user: dict = Depends(get_current_user)):
    import pandas as pd
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        df.describe().to_excel(writer, sheet_name="Statistics")
        cats = df.select_dtypes("object")
        if not cats.empty:
            cats.describe().to_excel(writer, sheet_name="Categories")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=data.xlsx"})


@router.post("/schedule", status_code=201)
def create_schedule(req: dict, user: dict = Depends(get_current_user)):
    from app.services.schedule_service import add
    s = add(user["email"], req.get("name","Report"), req.get("frequency","daily"),
            req.get("email",""), req.get("report_type","pdf"))
    return s


@router.get("/schedule")
def list_schedules(user: dict = Depends(get_current_user)):
    from app.services.schedule_service import get_all
    return get_all(user["email"])


@router.patch("/schedule/{schedule_id}")
def toggle_schedule(schedule_id: int, user: dict = Depends(get_current_user)):
    from app.services.schedule_service import toggle
    s = toggle(schedule_id, user["email"])
    if not s: raise HTTPException(404, "Schedule not found")
    return s


@router.delete("/schedule/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, user: dict = Depends(get_current_user)):
    from app.services.schedule_service import delete
    delete(schedule_id, user["email"])


@router.post("/schedule/run-all")
def run_all_schedules(user: dict = Depends(get_current_user)):
    """Trigger all active schedules for this user immediately."""
    from app.services.schedule_service import get_all
    schedules = get_all(user["email"])
    active = [s for s in schedules if s.get("active")]
    ran = []
    for s in active:
        try:
            df = get_df(user["email"])
            if df is not None:
                from services.agents.reports.pdf_generator import generate_pdf
                import sys, pathlib
                p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
                if p not in sys.path: sys.path.insert(0, p)
                pdf_bytes = generate_pdf(df, title=s.get("name","Report"))
                s["last_run"] = __import__("datetime").datetime.utcnow().isoformat()
                ran.append(s["name"])
        except Exception:
            pass
    return {"ran": len(ran), "schedules": ran}
