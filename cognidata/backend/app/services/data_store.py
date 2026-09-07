import os
import pathlib
import pandas as pd
import numpy as np
from typing import Optional
from cachetools import TTLCache

# ── Persistence directory ─────────────────────────────────────────────────────
_STORE_DIR = pathlib.Path(__file__).resolve().parents[2] / ".dataset_store"
_STORE_DIR.mkdir(exist_ok=True)

_store: dict[str, pd.DataFrame] = {}
_summary: dict[str, dict] = {}
_cache: TTLCache = TTLCache(maxsize=200, ttl=600)
_multi: dict[str, dict[str, pd.DataFrame]] = {}
_active: dict[str, str] = {}


# ── Disk helpers ──────────────────────────────────────────────────────────────

def _user_dir(user_id: str) -> pathlib.Path:
    d = _STORE_DIR / user_id.replace("@", "_at_").replace(".", "_")
    d.mkdir(exist_ok=True)
    return d


def _save_to_disk(user_id: str, name: str, df: pd.DataFrame) -> None:
    """Save dataframe to disk with proper error handling and logging."""
    try:
        p = _user_dir(user_id) / f"{name}.parquet"
        df.to_parquet(str(p), index=False)
    except Exception as e:
        # Log parquet failure
        print(f"Warning: Failed to save as parquet for {user_id}/{name}: {e}")
        # Fallback to CSV if parquet fails (e.g. unsupported dtypes)
        try:
            p = _user_dir(user_id) / f"{name}.csv"
            df.to_csv(str(p), index=False)
            print(f"Saved as CSV fallback: {user_id}/{name}")
        except Exception as csv_err:
            print(f"Error: Failed to save dataset {user_id}/{name}: {csv_err}")
            raise  # Re-raise to notify caller


def _load_from_disk(user_id: str, name: str) -> Optional[pd.DataFrame]:
    d = _user_dir(user_id)
    parquet = d / f"{name}.parquet"
    csv = d / f"{name}.csv"
    try:
        if parquet.exists():
            return pd.read_parquet(str(parquet))
        if csv.exists():
            return pd.read_csv(str(csv))
    except Exception:
        pass
    return None


def _delete_from_disk(user_id: str, name: str) -> None:
    d = _user_dir(user_id)
    for ext in (".parquet", ".csv"):
        p = d / f"{name}{ext}"
        if p.exists():
            try: p.unlink()
            except Exception: pass


def _save_active(user_id: str, name: str) -> None:
    try:
        (_user_dir(user_id) / "_active.txt").write_text(name, encoding="utf-8")
    except Exception:
        pass


def _load_active(user_id: str) -> Optional[str]:
    try:
        p = _user_dir(user_id) / "_active.txt"
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return None


def _list_disk_datasets(user_id: str) -> list[str]:
    """Return dataset names saved on disk for this user."""
    d = _user_dir(user_id)
    names = set()
    for f in d.iterdir():
        if f.suffix in (".parquet", ".csv") and not f.name.startswith("_"):
            names.add(f.stem)
    return sorted(names)


def _ensure_loaded(user_id: str) -> None:
    """Lazy-load datasets from disk into memory if not already loaded."""
    if user_id in _store:
        return
    disk_names = _list_disk_datasets(user_id)
    if not disk_names:
        return
    if user_id not in _multi:
        _multi[user_id] = {}
    for name in disk_names:
        if name not in _multi[user_id]:
            df = _load_from_disk(user_id, name)
            if df is not None:
                _multi[user_id][name] = df
    # Restore active
    active_name = _load_active(user_id)
    if active_name and active_name in _multi.get(user_id, {}):
        _store[user_id] = _multi[user_id][active_name]
        _summary[user_id] = _compute_summary(_multi[user_id][active_name])
        _active[user_id] = active_name
    elif _multi.get(user_id):
        first = next(iter(_multi[user_id]))
        _store[user_id] = _multi[user_id][first]
        _summary[user_id] = _compute_summary(_multi[user_id][first])
        _active[user_id] = first


# ── Public API ────────────────────────────────────────────────────────────────

def save(user_id: str, df: pd.DataFrame, name: str = "") -> None:
    _store[user_id] = df
    _summary[user_id] = _compute_summary(df)
    if user_id not in _multi:
        _multi[user_id] = {}
    key = name or f"dataset_{len(_multi[user_id]) + 1}"
    _multi[user_id][key] = df
    _active[user_id] = key
    # Persist to disk
    _save_to_disk(user_id, key, df)
    _save_active(user_id, key)
    # Invalidate AI cache
    keys = [k for k in list(_cache.keys()) if k.startswith(user_id)]
    for k in keys:
        try: del _cache[k]
        except: pass


def get(user_id: str) -> Optional[pd.DataFrame]:
    _ensure_loaded(user_id)
    return _store.get(user_id)


def get_summary(user_id: str) -> Optional[dict]:
    _ensure_loaded(user_id)
    return _summary.get(user_id)


def delete(user_id: str) -> None:
    # Delete all disk files for this user
    for name in _list_disk_datasets(user_id):
        _delete_from_disk(user_id, name)
    try:
        active_f = _user_dir(user_id) / "_active.txt"
        if active_f.exists(): active_f.unlink()
    except Exception:
        pass
    _store.pop(user_id, None)
    _summary.pop(user_id, None)
    _multi.pop(user_id, None)
    _active.pop(user_id, None)
    keys = [k for k in list(_cache.keys()) if k.startswith(user_id)]
    for k in keys:
        try: del _cache[k]
        except: pass


def get_ai_cache() -> TTLCache:
    return _cache


# ── Multi-dataset API ─────────────────────────────────────────────────────────

def list_datasets(user_id: str) -> list[dict]:
    _ensure_loaded(user_id)
    datasets = _multi.get(user_id, {})
    active = _active.get(user_id, "")
    result = []
    for name, df in datasets.items():
        result.append({
            "name": name,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "active": name == active,
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        })
    return result


def switch_dataset(user_id: str, name: str) -> bool:
    _ensure_loaded(user_id)
    datasets = _multi.get(user_id, {})
    if name not in datasets:
        return False
    _store[user_id] = datasets[name]
    _summary[user_id] = _compute_summary(datasets[name])
    _active[user_id] = name
    _save_active(user_id, name)
    keys = [k for k in list(_cache.keys()) if k.startswith(user_id)]
    for k in keys:
        try: del _cache[k]
        except: pass
    return True


def remove_dataset(user_id: str, name: str) -> bool:
    _ensure_loaded(user_id)
    datasets = _multi.get(user_id, {})
    if name not in datasets:
        return False
    del datasets[name]
    _delete_from_disk(user_id, name)
    if _active.get(user_id) == name:
        if datasets:
            new_active = next(iter(datasets))
            _store[user_id] = datasets[new_active]
            _summary[user_id] = _compute_summary(datasets[new_active])
            _active[user_id] = new_active
            _save_active(user_id, new_active)
        else:
            _store.pop(user_id, None)
            _summary.pop(user_id, None)
            _active.pop(user_id, None)
            try:
                (_user_dir(user_id) / "_active.txt").unlink(missing_ok=True)
            except Exception:
                pass
    return True


def _compute_summary(df: pd.DataFrame) -> dict:
    try:
        return {
            "columns": list(df.columns),
            "shape": df.shape,
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "missing": df.isnull().sum().to_dict(),
            "numeric_cols": df.select_dtypes(include=np.number).columns.tolist(),
            "category_cols": df.select_dtypes(include="object").columns.tolist(),
        }
    except Exception:
        return {"columns": list(df.columns), "shape": df.shape}
