"""Data routes - upload, preview, info, clean. JWT-protected, no API key needed."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.schemas.data import UploadResponse, PreviewResponse, InfoResponse, CleanResponse
from app.services import data_service

router = APIRouter(prefix="/data", tags=["Data"])


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload CSV, Excel, or JSON dataset. Stores in memory for this user session."""
    if not file.filename:
        raise HTTPException(400, "No file provided")
    return await data_service.load_file(file, user["email"])


@router.get("/preview", response_model=PreviewResponse)
def preview(n: int = 10, user: dict = Depends(get_current_user)):
    return data_service.get_preview(user["email"], n=min(n, 100))


@router.get("/info", response_model=InfoResponse)
def info(user: dict = Depends(get_current_user)):
    # Cache info for 30s - it's called on every page load
    from app.services.data_store import get_ai_cache
    _cache = get_ai_cache()
    key = f"info:{user['email']}"
    cached = _cache.get(key)
    if cached:
        return cached
    result = data_service.get_info(user["email"])
    try: _cache[key] = result
    except Exception: pass
    return result


@router.post("/clean", response_model=CleanResponse)
def clean(user: dict = Depends(get_current_user)):
    return data_service.clean_data(user["email"])


@router.delete("/clear", status_code=204)
def clear(user: dict = Depends(get_current_user)):
    """Remove the user's dataset from memory."""
    from app.services.data_store import delete
    delete(user["email"])


@router.get("/stats")
def stats(user: dict = Depends(get_current_user)):
    """Descriptive statistics per column."""
    import numpy as np
    df = _require(user["email"])
    desc = df.describe(include="all")
    return desc.replace({float("nan"): None}).to_dict()


def _require(user_id: str):
    from app.services.data_store import get
    df = get(user_id)
    if df is None:
        raise HTTPException(404, "No dataset found. Upload a file first.")
    return df


@router.get("/doctor")
def data_doctor(user: dict = Depends(get_current_user)):
    """Data quality health report."""
    import numpy as np
    df = _require(user["email"])

    # Missing values
    missing_cols = [(col, int(df[col].isnull().sum())) for col in df.columns if df[col].isnull().sum() > 0]

    # Duplicates
    dup_count = int(df.duplicated().sum())

    # Outliers (IQR)
    outlier_cols = []
    for col in df.select_dtypes(include=np.number).columns:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        n_out = int(((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum())
        if n_out > 0:
            outlier_cols.append({"column": col, "outliers": n_out})

    # Constant columns (only 1 unique value)
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]

    # Type mismatches - numeric stored as string
    type_mismatches = []
    for col in df.select_dtypes(include="object").columns:
        sample = df[col].dropna().head(100)
        numeric_count = sum(1 for v in sample if str(v).replace(".","",1).replace("-","",1).isdigit())
        if len(sample) > 0 and numeric_count / len(sample) > 0.8:
            type_mismatches.append({"column": col, "likely_type": "numeric", "sample": str(df[col].iloc[0])})

    # Health score
    issues = len(missing_cols) + (1 if dup_count > 0 else 0) + len(constant_cols) + len(type_mismatches)
    health_score = max(0, 100 - issues * 8)

    return {
        "health_score": health_score,
        "missing_cols": missing_cols,
        "duplicate_rows": dup_count,
        "outlier_cols": outlier_cols,
        "constant_cols": constant_cols,
        "type_mismatches": type_mismatches,
        "total_rows": len(df),
        "total_cols": len(df.columns),
    }


@router.post("/upload-clean")
async def upload_clean(user: dict = Depends(get_current_user)):
    """Mark current dataset as the cleaned version (already in memory)."""
    from app.services.data_store import get, save
    df = get(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset found")
    save(user["email"], df)
    return {"message": "Cleaned dataset saved", "rows": len(df), "columns": len(df.columns)}


@router.post("/snapshot")
def take_snapshot(user: dict = Depends(get_current_user)):
    """Record an observability snapshot of the current dataset."""
    import sys, pathlib
    df = _require(user["email"])
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)
    from agents.observability import take_snapshot, get_snapshots, compute_drift
    snap = take_snapshot(user["email"], df)
    drift = compute_drift(user["email"])
    return {"snapshot": snap, "drift": drift, "total_snapshots": len(get_snapshots(user["email"]))}


@router.get("/snapshots")
def list_snapshots(user: dict = Depends(get_current_user)):
    """List all observability snapshots for this user."""
    import sys, pathlib
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)
    from agents.observability import get_snapshots, compute_drift
    snaps = get_snapshots(user["email"])
    drift = compute_drift(user["email"])
    return {"snapshots": snaps, "drift": drift}


@router.delete("/snapshots")
def clear_snapshots(user: dict = Depends(get_current_user)):
    """Clear all observability snapshots."""
    import sys, pathlib
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)
    from agents.observability import clear_snapshots
    clear_snapshots(user["email"])
    return {"message": "Snapshots cleared"}


@router.post("/filter")
def filter_data(filters: dict, user: dict = Depends(get_current_user)):
    """Apply column filters and return filtered rows."""
    df = _require(user["email"])
    result = df.copy()
    for col, val in filters.items():
        if col not in result.columns or not val:
            continue
        if result[col].dtype == object:
            result = result[result[col].astype(str).str.contains(str(val), case=False, na=False)]
        else:
            try:
                result = result[result[col] == float(val)]
            except (ValueError, TypeError):
                pass
    return {"data": result.head(200).replace({float("nan"): None}).to_dict("records"), "total": len(result)}


# -- Multi-dataset endpoints ---------------------------------------------------

@router.post("/upload-multi")
@limiter.limit("5/minute")
async def upload_multi(
    request: Request,
    files: list[UploadFile] = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload up to 4 files at once. Each is stored separately; last one becomes active."""
    if not files:
        raise HTTPException(400, "No files provided")
    if len(files) > 4:
        raise HTTPException(400, "Maximum 4 files at a time")
    results = []
    for file in files:
        if not file.filename:
            continue
        try:
            result = await data_service.load_file(file, user["email"])
            results.append(result)
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})
    return {"uploaded": len(results), "files": results}


@router.get("/datasets")
def list_datasets(user: dict = Depends(get_current_user)):
    """List all uploaded datasets for this user."""
    from app.services.data_store import list_datasets as _list, _active
    datasets = _list(user["email"])
    active = _active.get(user["email"], "")
    # Return names list + active for frontend compatibility
    names = [d["name"] for d in datasets]
    return {"datasets": names, "active": active, "details": datasets}


@router.post("/datasets/switch")
def switch_dataset(name: str, user: dict = Depends(get_current_user)):
    """Switch the active dataset by name."""
    from app.services.data_store import switch_dataset as _switch
    if not _switch(user["email"], name):
        raise HTTPException(404, f"Dataset '{name}' not found")
    return {"message": f"Switched to '{name}'", "active": name}


@router.delete("/datasets/{name}", status_code=204)
def remove_dataset(name: str, user: dict = Depends(get_current_user)):
    """Remove a specific dataset by name."""
    from app.services.data_store import remove_dataset as _remove
    if not _remove(user["email"], name):
        raise HTTPException(404, f"Dataset '{name}' not found")
