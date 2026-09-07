"""Report schedule store + APScheduler execution."""
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

_schedules: list[dict] = []
_next_id = 1
_scheduler = None


def add(user_id: str, name: str, frequency: str, email: str, report_type: str = "pdf") -> dict:
    global _next_id
    s = {"id": _next_id, "user": user_id, "name": name, "frequency": frequency,
         "email": email, "report_type": report_type, "active": True,
         "created": datetime.now(timezone.utc).isoformat(), "last_run": None}
    _schedules.append(s)
    _next_id += 1
    _sync_scheduler()
    return s


def get_all(user_id: str) -> list[dict]:
    return [s for s in _schedules if s["user"] == user_id]


def toggle(schedule_id: int, user_id: str) -> dict | None:
    for s in _schedules:
        if s["id"] == schedule_id and s["user"] == user_id:
            s["active"] = not s["active"]
            _sync_scheduler()
            return s
    return None


def delete(schedule_id: int, user_id: str) -> bool:
    global _schedules
    before = len(_schedules)
    _schedules = [s for s in _schedules if not (s["id"] == schedule_id and s["user"] == user_id)]
    _sync_scheduler()
    return len(_schedules) < before


# ── APScheduler integration ───────────────────────────────────────────────────

def _freq_to_trigger(frequency: str):
    """Convert frequency string to APScheduler trigger kwargs."""
    f = frequency.lower()
    if f == "hourly":
        return "interval", {"hours": 1}
    elif f == "daily":
        return "cron", {"hour": 8, "minute": 0}   # 08:00 UTC daily
    elif f == "weekly":
        return "cron", {"day_of_week": "mon", "hour": 8, "minute": 0}
    elif f == "monthly":
        return "cron", {"day": 1, "hour": 8, "minute": 0}
    else:
        return "interval", {"hours": 24}


def _run_schedule(schedule_id: int):
    """Execute a single schedule — generate PDF and email it."""
    s = next((x for x in _schedules if x["id"] == schedule_id), None)
    if not s or not s.get("active"):
        return
    try:
        from app.services.data_store import get as get_df
        import sys, pathlib
        p = str(pathlib.Path(__file__).resolve().parents[2] / "services")
        if p not in sys.path:
            sys.path.insert(0, p)

        df = get_df(s["user"])
        if df is None:
            logger.warning(f"Schedule {schedule_id}: no dataset for user {s['user']}")
            return

        from agents.reports.pdf_generator import generate_pdf
        pdf_bytes = generate_pdf(df, title=s.get("name", "Scheduled Report"))

        # Email the PDF
        if s.get("email"):
            try:
                from app.services.email_service import send_async
                body = f"<p>Your scheduled report <b>{s['name']}</b> is attached.</p>"
                send_async(s["email"], f"Scheduled Report: {s['name']}", body,
                           attachments=[{"filename": f"{s['name']}.pdf",
                                         "data": pdf_bytes,
                                         "mime": "application/pdf"}])
            except Exception as e:
                logger.warning(f"Schedule {schedule_id} email failed: {e}")

        s["last_run"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Schedule '{s['name']}' ran successfully")

    except Exception as e:
        logger.error(f"Schedule {schedule_id} execution error: {e}")


def _sync_scheduler():
    """Add/remove APScheduler jobs to match active schedules."""
    global _scheduler
    if _scheduler is None:
        return
    active_ids = {s["id"] for s in _schedules if s.get("active")}
    existing_ids = {int(j.id) for j in _scheduler.get_jobs() if j.id.isdigit()}

    # Remove jobs for deleted/inactive schedules
    for jid in existing_ids - active_ids:
        try:
            _scheduler.remove_job(str(jid))
        except Exception:
            pass

    # Add jobs for new active schedules
    for s in _schedules:
        if not s.get("active"):
            continue
        sid = str(s["id"])
        if s["id"] not in existing_ids:
            try:
                trigger_type, trigger_kwargs = _freq_to_trigger(s.get("frequency", "daily"))
                _scheduler.add_job(
                    _run_schedule,
                    trigger_type,
                    id=sid,
                    args=[s["id"]],
                    replace_existing=True,
                    **trigger_kwargs,
                )
                logger.info(f"Scheduled job '{s['name']}' ({trigger_type} {trigger_kwargs})")
            except Exception as e:
                logger.warning(f"Failed to schedule job {sid}: {e}")


def start_scheduler():
    """Start the APScheduler background scheduler."""
    global _scheduler
    if _scheduler is not None:
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.start()
        _sync_scheduler()
        logger.info("✅ APScheduler started")
    except ImportError:
        logger.warning("apscheduler not installed — report scheduling disabled. Run: pip install apscheduler")
    except Exception as e:
        logger.error(f"Scheduler start failed: {e}")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None
