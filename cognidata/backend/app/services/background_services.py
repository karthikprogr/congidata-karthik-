"""
Background Services — daemon threads started on app startup.
- Performance Agent: memory monitoring, GC, cache cleanup
- Report Scheduler: checks due schedules every 60s
- Geo Stream: already auto-starts in geo_agent.py
"""
import gc
import os
import sys
import time
import threading
import pathlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Performance Agent ─────────────────────────────────────────────────────────

_perf_running = False
_perf_thread = None
_perf_events: list[dict] = []
_perf_config = {
    "check_interval": 30,
    "memory_warn_mb": 400,
    "memory_gc_mb": 600,
}


def _perf_loop():
    """Performance monitoring daemon."""
    checks = 0
    _db_optimize_checks = 0  # every 720 checks @ 30s = 6h
    while _perf_running:
        try:
            checks += 1
            _db_optimize_checks += 1
            ts = datetime.now(timezone.utc).isoformat()

            # Memory check
            try:
                import psutil
                proc = psutil.Process()
                mem_mb = proc.memory_info().rss / 1024 / 1024
                if mem_mb > _perf_config["memory_gc_mb"]:
                    gc.collect()
                    _perf_events.append({"ts": ts, "level": "WARN", "message": f"GC triggered at {mem_mb:.0f}MB"})
                elif mem_mb > _perf_config["memory_warn_mb"]:
                    _perf_events.append({"ts": ts, "level": "WARN", "message": f"High memory: {mem_mb:.0f}MB"})
                else:
                    _perf_events.append({"ts": ts, "level": "OK", "message": f"Memory OK: {mem_mb:.0f}MB"})
            except ImportError:
                pass

            # Temp file cleanup every 10 checks (~5 min)
            if checks % 10 == 0:
                try:
                    import tempfile, glob
                    pattern = os.path.join(tempfile.gettempdir(), "cognidata_*.pkl")
                    old_files = [f for f in glob.glob(pattern) if time.time() - os.path.getmtime(f) > 86400]
                    for f in old_files:
                        try: os.remove(f)
                        except: pass
                    if old_files:
                        _perf_events.append({"ts": ts, "level": "OK", "message": f"Cleaned {len(old_files)} temp files"})
                except Exception:
                    pass

            # DB optimize every 720 checks = 6 hours
            if _db_optimize_checks >= 720:
                _db_optimize_checks = 0
                try:
                    from app.core.database import engine
                    from sqlalchemy import text, inspect as sa_inspect
                    with engine.connect() as conn:
                        if "sqlite" in str(engine.url):
                            conn.execute(text("PRAGMA optimize"))
                        else:
                            tables = sa_inspect(engine).get_table_names()
                            for t in tables:
                                try: conn.execute(text(f"OPTIMIZE TABLE `{t}`"))
                                except: pass
                        conn.commit()
                    _perf_events.append({"ts": ts, "level": "OK", "message": "DB optimized (6h cycle)"})
                except Exception as e:
                    _perf_events.append({"ts": ts, "level": "WARN", "message": f"DB optimize skipped: {e}"})

            # Keep only last 100 events
            if len(_perf_events) > 100:
                _perf_events[:] = _perf_events[-100:]

        except Exception as e:
            _perf_events.append({"ts": datetime.now(timezone.utc).isoformat(), "level": "ERROR", "message": str(e)})

        time.sleep(_perf_config["check_interval"])


def start_performance_agent():
    global _perf_running, _perf_thread
    if _perf_running:
        return
    _perf_running = True
    _perf_thread = threading.Thread(target=_perf_loop, daemon=True, name="perf-agent")
    _perf_thread.start()
    logger.info("✅ Performance Agent started")


def stop_performance_agent():
    global _perf_running
    _perf_running = False


def get_perf_events(limit: int = 30) -> list[dict]:
    return list(reversed(_perf_events))[:limit]


def get_perf_metrics() -> dict:
    metrics = {"uptime": f"{round(time.time() - _start_time)}s", "checks": len(_perf_events)}
    try:
        import psutil
        proc = psutil.Process()
        metrics["memory_mb"] = round(proc.memory_info().rss / 1024 / 1024, 1)
        metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)
    except ImportError:
        pass
    return metrics


_start_time = time.time()


# ── Report Scheduler ──────────────────────────────────────────────────────────

_sched_running = False


def start_report_scheduler():
    global _sched_running
    if _sched_running:
        return
    _sched_running = True
    from app.services.schedule_service import start_scheduler
    start_scheduler()
    logger.info("✅ Report Scheduler (APScheduler) started")


def stop_report_scheduler():
    global _sched_running
    _sched_running = False
    from app.services.schedule_service import stop_scheduler
    stop_scheduler()


# ── Geo Stream ────────────────────────────────────────────────────────────────

def start_geo_stream():
    """Start the geo simulation (already auto-starts on import, but ensure it's running)."""
    try:
        p = str(pathlib.Path(__file__).resolve().parents[2] / "services")
        if p not in sys.path:
            sys.path.insert(0, p)
        from agents.geo.geo_agent import start_simulation
        start_simulation()
        logger.info("✅ Geo Stream started")
    except Exception as e:
        logger.warning(f"Geo stream start: {e}")


# ── Start All ─────────────────────────────────────────────────────────────────

def start_all():
    """Start all background services."""
    start_performance_agent()
    start_report_scheduler()
    start_geo_stream()
    logger.info("✅ All background services started")
