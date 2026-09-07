import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.api.router import api_router
from app.core.database import Base, engine
from app.models import user  # noqa
from app.models import workspace  # noqa

# ── Ensure MySQL database exists ──────────────────────────────────────────────
def _ensure_db():
    from app.core.config import DATABASE_URL
    if "mysql" in DATABASE_URL:
        try:
            import pymysql, re
            m = re.match(r"mysql\+pymysql://([^:]+):([^@]*)@([^:/]+):?(\d+)?/(\w+)", DATABASE_URL)
            if m:
                user_, pwd, host, port, dbname = m.groups()
                conn = pymysql.connect(host=host, user=user_, password=pwd,
                                       port=int(port or 3306))
                conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.commit(); conn.close()
                print(f"✅ MySQL database '{dbname}' ready")
        except Exception as e:
            print(f"DB ensure warning: {e}")

_ensure_db()

Base.metadata.create_all(bind=engine)

# ── DB migrations (safe, idempotent — works on SQLite + MySQL) ────────────────
def _migrate():
    """Add any missing columns to existing tables without dropping data."""
    from sqlalchemy import text, inspect
    try:
        insp = inspect(engine)
        existing = {c["name"] for c in insp.get_columns("users")}
        with engine.connect() as conn:
            if "name" not in existing:
                if "sqlite" in str(engine.url):
                    conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(255)"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(255) NULL"))
                conn.commit()
                print("✅ Migration: added users.name column")
            if "active" not in existing:
                if "sqlite" in str(engine.url):
                    conn.execute(text("ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT 1"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN active TINYINT(1) NOT NULL DEFAULT 1"))
                conn.commit()
                print("✅ Migration: added users.active column")
    except Exception as e:
        print(f"Migration note: {e}")

_migrate()

app = FastAPI(title="COGNIDATA API", version="2.0.0")
app.add_middleware(GZipMiddleware, minimum_size=500)  # compress responses > 500 bytes
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup():
    # Seed database
    try:
        from app.seed import seed
        seed()
    except Exception as e:
        print(f"Seed error: {e}")

    # Start background services
    try:
        from app.services.background_services import start_all
        start_all()
    except Exception as e:
        print(f"Background services error: {e}")

from app.services import log_service as _log_svc

@app.middleware("http")
async def timing(request: Request, call_next):
    t = time.monotonic()
    resp = await call_next(request)
    ms = (time.monotonic() - t) * 1000
    # Add cache headers for read-only GET endpoints
    if request.method == "GET" and resp.status_code == 200:
        path = request.url.path
        if any(p in path for p in ["/data/info", "/data/stats", "/viz/overview", "/analytics/stats"]):
            resp.headers["Cache-Control"] = "private, max-age=30"
        elif any(p in path for p in ["/workspaces", "/profile", "/alerts", "/roadmap"]):
            resp.headers["Cache-Control"] = "private, max-age=10"
    try:
        _log_svc.record_request(request.url.path, request.method, ms, resp.status_code)
    except Exception:
        pass
    return resp

app.include_router(api_router)
