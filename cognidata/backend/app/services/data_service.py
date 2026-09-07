import io
import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile
from app.services import data_store

SUPPORTED = {"csv", "xlsx", "xls", "json"}

async def load_file(file: UploadFile, user_id: str) -> dict:
    # Sanitize filename to prevent path traversal
    filename = (file.filename or "dataset").replace("/", "_").replace("\\", "_").replace("..", "_")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED:
        raise HTTPException(400, f"Unsupported format: .{ext}. Supported: {', '.join(SUPPORTED)}")
    
    # Enforce 200MB limit BEFORE reading entire file
    MAX_SIZE = 200 * 1024 * 1024  # 200MB
    
    # Stream read with size limit to prevent memory exhaustion
    raw = bytearray()
    chunk_count = 0
    while True:
        try:
            chunk = await file.read(8192)  # 8KB chunks
            if not chunk:
                break
            raw.extend(chunk)
            chunk_count += 1
            if len(raw) > MAX_SIZE:
                raise HTTPException(413, f"File too large. Maximum is 200MB.")
        except HTTPException:
            raise
        except Exception as read_err:
            raise HTTPException(500, f"Error reading file: {str(read_err)[:100]}")
    
    if len(raw) == 0:
        raise HTTPException(422, "File is empty")
    
    # Convert to bytes for pandas
    raw_bytes = bytes(raw)
    
    try:
        if ext == "csv":
            try: 
                df = pd.read_csv(io.BytesIO(raw_bytes))
            except UnicodeDecodeError: 
                try:
                    df = pd.read_csv(io.BytesIO(raw_bytes), encoding="latin1")
                except Exception:
                    try:
                        df = pd.read_csv(io.BytesIO(raw_bytes), encoding="iso-8859-1")
                    except Exception:
                        raise HTTPException(422, "Could not decode CSV file. Please ensure it's a valid UTF-8, Latin-1, or ISO-8859-1 encoded text file.")
        elif ext in ("xlsx", "xls"): 
            try:
                df = pd.read_excel(io.BytesIO(raw_bytes), engine="openpyxl" if ext == "xlsx" else "xlrd")
            except Exception as excel_err:
                raise HTTPException(422, f"Could not parse Excel file: {str(excel_err)[:150]}. Ensure it's a valid Excel file.")
        elif ext == "json":
            try:
                df = pd.read_json(io.BytesIO(raw_bytes))
            except Exception as json_err:
                raise HTTPException(422, f"Could not parse JSON file: {str(json_err)[:150]}. Ensure it's valid JSON.")
        else:
            raise HTTPException(400, f"Unsupported format: .{ext}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(422, f"Could not parse file: {str(e)[:200]}")
    
    if df.empty or len(df) == 0: 
        raise HTTPException(422, "File is empty or contains no valid data")
    
    # Downcast to save memory (with error handling)
    try:
        for col in df.select_dtypes("int64").columns:  
            df[col] = pd.to_numeric(df[col], downcast="integer")
        for col in df.select_dtypes("float64").columns: 
            df[col] = pd.to_numeric(df[col], downcast="float")
    except Exception:
        pass  # Silently skip downcasting if it fails
    
    # Save with sanitized filename
    data_store.save(user_id, df, name=filename)
    
    # Auto snapshot for observability
    try:
        from app.services.log_service import log_event
        log_event(user_id, "dataset_upload", f"{filename} — {len(df)} rows × {len(df.columns)} cols")
    except Exception:
        pass
    
    return {
        "message": "Uploaded successfully", 
        "filename": filename,
        "rows": len(df), 
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3)
    }

def get_preview(user_id: str, n: int = 10) -> dict:
    df = _require(user_id)
    return {"data": df.head(n).replace({np.nan: None}).to_dict("records"), "total_rows": len(df)}

def get_info(user_id: str) -> dict:
    df = _require(user_id)
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    cols_info = [{"name": c, "dtype": str(df[c].dtype), "nulls": int(df[c].isnull().sum()), "unique": int(df[c].nunique())} for c in df.columns]
    return {
        "rows": len(df), "columns": len(df.columns),
        "column_names": list(df.columns),
        "columns_info": cols_info,
        "numeric_columns": num_cols,
        "categorical_columns": cat_cols,
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3),
    }

def clean_data(user_id: str) -> dict:
    df = _require(user_id)
    before = len(df); nulls_before = int(df.isnull().sum().sum())
    df = df.drop_duplicates()
    rows_removed = before - len(df)
    num = df.select_dtypes(include=np.number).columns
    df[num] = df[num].fillna(df[num].mean())
    for col in df.select_dtypes("object").columns:
        mode = df[col].mode()
        df[col] = df[col].fillna(mode[0] if not mode.empty else "Unknown")
    nulls_filled = nulls_before - int(df.isnull().sum().sum())
    data_store.save(user_id, df)
    return {"message": "Cleaned", "rows_before": before, "rows_after": len(df),
            "rows_removed": rows_removed, "nulls_filled": nulls_filled}

def _require(user_id: str) -> pd.DataFrame:
    df = data_store.get(user_id)
    if df is None: raise HTTPException(404, "No dataset found. Upload a file first.")
    return df
