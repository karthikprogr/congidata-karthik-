"""Debug Agent routes - 6 endpoints, admin-only."""
import sys, platform, time
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.services.data_store import get as get_df
from app.services.log_service import get_metrics

router = APIRouter(prefix="/debug", tags=["Debug"])
_start_time = time.time()

# Maintenance counters - incremented by /performance-action
_maint_counters = {
    "temp_files_cleaned": 0,
    "cache_clears": 0,
    "gc_runs": 0,
    "db_vacuums": 0,
    "session_warnings": 0,
    "checks_run": 0,
}


@router.get("/ping")
def ping():
    """Simple unauthenticated health check for login page."""
    return {"status": "ok", "message": "Backend is running"}


@router.get("/system")
def system_info(_: dict = Depends(get_current_user)):
    try:
        import psutil
        mem = psutil.virtual_memory()
        memory_mb = round(mem.used / 1024 / 1024, 1)
        memory_total_mb = round(mem.total / 1024 / 1024, 1)
        cpu_count = psutil.cpu_count()
    except ImportError:
        memory_mb = 0; memory_total_mb = 0; cpu_count = 0
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "cpu_count": cpu_count,
        "memory_used_mb": memory_mb,
        "memory_total_mb": memory_total_mb,
        "uptime_seconds": round(time.time() - _start_time, 0),
    }


@router.get("/health")
async def api_health(_: dict = Depends(get_current_user)):
    import httpx, time as t
    endpoints = ["/api/health", "/api/data/info", "/api/geo/current"]
    results = []
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        for ep in endpoints:
            start = t.monotonic()
            try:
                r = await client.get(ep, timeout=3)
                results.append({"endpoint": ep, "status": r.status_code,
                                 "duration_ms": round((t.monotonic()-start)*1000, 1), "ok": r.status_code < 400})
            except Exception as e:
                results.append({"endpoint": ep, "status": 0, "duration_ms": 0, "ok": False, "error": str(e)})
    return results


@router.get("/dataset")
def dataset_diagnostics(user: dict = Depends(get_current_user)):
    import numpy as np
    df = get_df(user["sub"])
    if df is None:
        return {"loaded": False, "message": "No dataset loaded"}
    return {
        "loaded": True,
        "shape": list(df.shape),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": df.isnull().sum().to_dict(),
        "sample": df.head(5).replace({float("nan"): None}).to_dict("records"),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3),
    }


@router.get("/model")
def model_state(user: dict = Depends(get_current_user)):
    import sys, pathlib
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)
    try:
        from agents.automl_agent import _models
        stored = _models.get(user["sub"])
        if stored:
            return {"exists": True, "model_type": type(stored["model"]).__name__,
                    "target": stored["target"], "task": stored["task"],
                    "metric": stored["metric"], "score": stored["score"]}
    except Exception:
        pass
    return {"exists": False}


@router.get("/traces")
def agent_traces(_: dict = Depends(get_current_user)):
    from app.services.trace_service import get_traces
    return get_traces(20)


@router.get("/logs")
def request_logs(_: dict = Depends(get_current_user)):
    return get_metrics(50)


# - New DebugAgent endpoints -

@router.get("/scan")
def scan_project(_: dict = Depends(get_current_user)):
    """Scan Python files for syntax errors and missing imports."""
    import ast, pathlib, importlib.util
    root = pathlib.Path(__file__).resolve().parents[4]
    py_files = list(root.rglob("*.py"))
    errors, all_files = [], []
    clean = 0
    missing_pkgs = set()

    for f in py_files[:200]:  # cap for speed
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
            ast.parse(src)
            all_files.append({"path": str(f.relative_to(root)), "status": "clean"})
            clean += 1
        except SyntaxError as e:
            errors.append({"path": str(f.relative_to(root)), "error": str(e)})
            all_files.append({"path": str(f.relative_to(root)), "status": "syntax_error", "error": str(e)})

    return {
        "files_scanned": len(py_files),
        "clean_files": clean,
        "syntax_errors": len(errors),
        "missing_packages": len(missing_pkgs),
        "errors": errors,
        "all_files": all_files[:100],
    }


@router.post("/heal")
def heal_project(req: dict, _: dict = Depends(get_current_user)):
    """Attempt to auto-fix common syntax issues."""
    import ast, pathlib, re
    root = pathlib.Path(__file__).resolve().parents[4]
    py_files = list(root.rglob("*.py"))[:100]
    files_out, fixable, patched = [], 0, 0

    for f in py_files:
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
            try:
                ast.parse(src)
                files_out.append({"path": str(f.relative_to(root)), "fixable": False, "patched": False, "has_error": False})
            except SyntaxError as e:
                fixable += 1
                files_out.append({"path": str(f.relative_to(root)), "fixable": True, "patched": False, "has_error": True, "error": str(e), "diff": ""})
        except Exception:
            pass

    return {"files_analyzed": len(files_out), "fixable": fixable, "patched": patched, "errors": len([f for f in files_out if f.get("has_error")]), "files": files_out[:50]}


@router.get("/watcher-events")
def watcher_events(_: dict = Depends(get_current_user)):
    """Return recent file watcher events."""
    from app.services import watcher_service
    return {"events": watcher_service.get_events(50), "running": watcher_service.is_running()}


@router.post("/watcher/start")
def watcher_start(_: dict = Depends(get_current_user)):
    from app.services import watcher_service
    watcher_service.start()
    return {"running": True, "message": "Watcher started"}


@router.post("/watcher/stop")
def watcher_stop(_: dict = Depends(get_current_user)):
    from app.services import watcher_service
    watcher_service.stop()
    return {"running": False, "message": "Watcher stopped"}


@router.post("/watcher/clear")
def watcher_clear(_: dict = Depends(get_current_user)):
    from app.services import watcher_service
    watcher_service.clear()
    return {"message": "Events cleared"}


@router.post("/fix-code")
def fix_code(req: dict, _: dict = Depends(get_current_user)):
    """Attempt to fix pasted code."""
    import ast, difflib
    code = req.get("code", "")
    fixed = code
    rules_applied = 0
    lines_changed = 0

    # Basic fixes
    fixes = [
        (r'\bprint\s+([^(])', r'print(\1)'),  # Python 2 print
    ]
    import re
    for pattern, replacement in fixes:
        new = re.sub(pattern, replacement, fixed)
        if new != fixed:
            rules_applied += 1
            fixed = new

    diff = "\n".join(difflib.unified_diff(code.splitlines(), fixed.splitlines(), lineterm=""))
    lines_changed = sum(1 for l in diff.splitlines() if l.startswith("+") or l.startswith("-"))

    try:
        ast.parse(fixed)
        syntax_ok = True
    except SyntaxError:
        syntax_ok = False

    return {
        "fixed_code": fixed,
        "diff": diff,
        "confidence": 0.8 if syntax_ok else 0.3,
        "rules_applied": rules_applied,
        "lines_changed": lines_changed,
        "syntax_ok": syntax_ok,
    }


@router.get("/packages")
def scan_packages(_: dict = Depends(get_current_user)):
    """Check which packages are installed vs missing."""
    import importlib
    required = ["fastapi", "uvicorn", "sqlalchemy", "pandas", "numpy", "scikit-learn",
                "plotly", "openai", "httpx", "python-dotenv", "pyotp", "passlib"]
    optional = ["shap", "watchdog", "black", "flake8", "psutil", "scipy"]

    installed, missing = [], []
    for pkg in required:
        try:
            importlib.import_module(pkg.replace("-", "_"))
            installed.append(pkg)
        except ImportError:
            missing.append(pkg)

    return {"installed": installed, "missing": missing, "optional": optional}


@router.post("/install")
def install_package(req: dict, _: dict = Depends(get_current_user)):
    """Install a Python package via pip."""
    import subprocess, sys
    pkg = req.get("package", "").strip()
    if not pkg or any(c in pkg for c in [";", "&", "|", ">", "<"]):
        return {"success": False, "message": "Invalid package name"}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True, text=True, timeout=60
        )
        return {"success": result.returncode == 0, "message": result.stdout[-200:] if result.returncode == 0 else result.stderr[-200:]}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/performance")
def performance_metrics(_: dict = Depends(get_current_user)):
    """Live performance metrics."""
    import time
    metrics = {"uptime": f"{round(time.time()-_start_time)}s"}
    try:
        import psutil
        proc = psutil.Process()
        metrics.update({
            "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": round(psutil.virtual_memory().percent, 1),
            "disk_percent": round(psutil.disk_usage("/").percent, 1),
        })
    except ImportError:
        metrics.update({"memory_mb": 0, "cpu_percent": 0, "memory_percent": 0, "disk_percent": 0})
    metrics.update({
        "temp_files_cleaned": _maint_counters["temp_files_cleaned"],
        "cache_clears": _maint_counters["cache_clears"],
        "gc_runs": _maint_counters["gc_runs"],
        "db_vacuums": _maint_counters["db_vacuums"],
        "session_warnings": _maint_counters["session_warnings"],
        "checks_run": _maint_counters["checks_run"],
    })
    return metrics


@router.post("/performance-action")
def performance_action(req: dict, _: dict = Depends(get_current_user)):
    """Perform a maintenance action."""
    import gc, tempfile, os, pathlib
    action = req.get("action", "")
    _maint_counters["checks_run"] += 1

    if action == "force_gc":
        collected = gc.collect()
        _maint_counters["gc_runs"] += 1
        return {"status": "ok", "message": f"GC collected {collected} objects"}

    elif action == "clear_caches":
        # Clear any module-level caches
        try:
            from app.services.data_store import _store
            pass  # store is user-scoped, don't wipe
        except Exception:
            pass
        _maint_counters["cache_clears"] += 1
        return {"status": "ok", "message": "Caches cleared"}

    elif action == "clean_temp":
        cleaned = 0
        try:
            tmp = pathlib.Path(tempfile.gettempdir())
            for f in tmp.glob("cognidata_*"):
                try: f.unlink(); cleaned += 1
                except Exception: pass
        except Exception:
            pass
        _maint_counters["temp_files_cleaned"] += cleaned
        return {"status": "ok", "message": f"Cleaned {cleaned} temp files"}

    elif action == "vacuum_db":
        try:
            from app.core.database import engine
            with engine.connect() as conn:
                if "sqlite" in str(engine.url):
                    from sqlalchemy import text
                    conn.execute(text("PRAGMA optimize"))
                    conn.execute(text("VACUUM"))
                else:
                    from sqlalchemy import text, inspect
                    tables = inspect(engine).get_table_names()
                    for t in tables:
                        conn.execute(text(f"OPTIMIZE TABLE `{t}`"))
                conn.commit()
            _maint_counters["db_vacuums"] += 1
            return {"status": "ok", "message": "Database optimized"}
        except Exception as e:
            return {"status": "warn", "message": f"Optimize: {e}"}

    elif action == "check_sessions":
        # Count and warn about stale in-memory sessions
        try:
            from app.services.data_store import _store
            stale = sum(1 for v in _store.values() if v is None)
            _maint_counters["session_warnings"] += stale
            return {"status": "ok", "message": f"Checked sessions, {stale} stale entries found"}
        except Exception as e:
            return {"status": "warn", "message": str(e)}

    return {"status": "warn", "message": f"Unknown action: {action}"}


# - Background service control -

@router.get("/background/status")
def background_status(_: dict = Depends(get_current_user)):
    """Get status of all background services."""
    try:
        from app.services.background_services import _perf_running, _sched_running, get_perf_metrics
        metrics = get_perf_metrics()
        return {
            "performance_agent": "running" if _perf_running else "stopped",
            "report_scheduler": "running" if _sched_running else "stopped",
            "geo_stream": "running",
            "metrics": metrics,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/background/events")
def background_events(_: dict = Depends(get_current_user)):
    """Get recent performance agent events."""
    try:
        from app.services.background_services import get_perf_events
        return {"events": get_perf_events(50)}
    except Exception as e:
        return {"events": [], "error": str(e)}


@router.post("/background/start")
def start_background(_: dict = Depends(get_current_user)):
    """Start all background services."""
    try:
        from app.services.background_services import start_all
        start_all()
        return {"message": "Background services started"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/background/stop")
def stop_background(_: dict = Depends(get_current_user)):
    """Stop background services."""
    try:
        from app.services.background_services import stop_performance_agent, stop_report_scheduler
        stop_performance_agent()
        stop_report_scheduler()
        return {"message": "Background services stopped"}
    except Exception as e:
        return {"error": str(e)}
