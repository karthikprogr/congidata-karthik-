"""File watcher service — monitors Python files for changes using watchdog."""
import ast
import threading
import pathlib
from datetime import datetime, timezone

_events: list[dict] = []
_running = False
_observer = None
_lock = threading.Lock()


def _record(path: str, event_type: str, confidence: float = 1.0, patched: bool = False, diff: str = ""):
    with _lock:
        _events.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "filename": path,
            "event_type": event_type,
            "confidence": confidence,
            "patched": patched,
            "diff": diff,
        })
        if len(_events) > 200:
            _events.pop(0)


def _check_file(path: str) -> dict:
    """Check a Python file for syntax errors."""
    try:
        src = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
        ast.parse(src)
        return {"ok": True, "error": None}
    except SyntaxError as e:
        return {"ok": False, "error": str(e)}


def start():
    global _running, _observer
    if _running:
        return
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        root = str(pathlib.Path(__file__).resolve().parents[3])

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.is_directory or not event.src_path.endswith(".py"):
                    return
                result = _check_file(event.src_path)
                rel = event.src_path.replace(root, "").lstrip("/\\")
                _record(rel, "modified", confidence=1.0 if result["ok"] else 0.3,
                        patched=False, diff=result.get("error") or "")

            def on_created(self, event):
                if event.is_directory or not event.src_path.endswith(".py"):
                    return
                rel = event.src_path.replace(root, "").lstrip("/\\")
                _record(rel, "created")

        _observer = Observer()
        _observer.schedule(Handler(), root, recursive=True)
        _observer.start()
        _running = True
        _record("watcher", "started", confidence=1.0)
    except ImportError:
        _record("watcher", "error — watchdog not installed. Run: pip install watchdog")
    except Exception as e:
        _record("watcher", f"error: {e}")


def stop():
    global _running, _observer
    if _observer:
        try:
            _observer.stop()
            _observer.join(timeout=2)
        except Exception:
            pass
        _observer = None
    _running = False
    _record("watcher", "stopped")


def is_running() -> bool:
    return _running


def get_events(limit: int = 50) -> list[dict]:
    with _lock:
        return list(reversed(_events))[:limit]


def clear():
    with _lock:
        _events.clear()
