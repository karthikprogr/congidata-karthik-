"""
COGNIDATA — Full Database Setup & Verification Script
Run from: cognidata/backend/
Usage:  python setup_db.py
"""
import os, sys, sqlite3, pathlib
from datetime import datetime, timezone

# ── Load env ──────────────────────────────────────────────────────────────────
env_path = pathlib.Path(__file__).parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(str(env_path))
    print(f"✅ Loaded .env from {env_path}")
else:
    print("⚠️  No .env found — using defaults")

# ── Add app to path ───────────────────────────────────────────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from app.core.config import DATABASE_URL, ADMIN_EMAIL, SECRET_KEY
from app.core.database import Base, engine, SessionLocal
from app.models import user, workspace  # noqa — register models

STEP = 1
def step(msg):
    global STEP
    print(f"\n{'─'*55}")
    print(f"  Step {STEP}: {msg}")
    print(f"{'─'*55}")
    STEP += 1

# ═══════════════════════════════════════════════════════
# STEP 1 — Create all tables
# ═══════════════════════════════════════════════════════
step("Creating all database tables")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created (or already exist)")
except Exception as e:
    print(f"❌ Table creation failed: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════
# STEP 2 — Run migrations (add missing columns safely)
# ═══════════════════════════════════════════════════════
step("Running safe column migrations")
from sqlalchemy import text, inspect

def migrate():
    insp = inspect(engine)
    with engine.connect() as conn:
        is_sqlite = "sqlite" in str(engine.url)

        # ── users table ──────────────────────────────
        user_cols = {c["name"] for c in insp.get_columns("users")}
        migrations = {
            "name":         "VARCHAR(255)",
            "active":       "BOOLEAN DEFAULT 1" if is_sqlite else "TINYINT(1) NOT NULL DEFAULT 1",
            "totp_secret":  "VARCHAR(64)",
            "totp_enabled": "BOOLEAN DEFAULT 0",
            "created_at":   "VARCHAR(64)",
            "avatar_url":   "VARCHAR(512)",
            "bio":          "TEXT",
        }
        for col, col_def in migrations.items():
            if col not in user_cols:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_def}"))
                    conn.commit()
                    print(f"  ✅ Added users.{col}")
                except Exception as e:
                    print(f"  ⚠️  users.{col}: {e}")

        # ── workspaces table ──────────────────────────
        ws_cols = {c["name"] for c in insp.get_columns("workspaces")}
        ws_migrations = {
            "created_at":  "VARCHAR(64)",
            "description": "VARCHAR(1000) DEFAULT ''",
            "color":       "VARCHAR(16) DEFAULT '#6366f1'",
            "icon":        "VARCHAR(16) DEFAULT '🧠'",
        }
        for col, col_def in ws_migrations.items():
            if col not in ws_cols:
                try:
                    conn.execute(text(f"ALTER TABLE workspaces ADD COLUMN {col} {col_def}"))
                    conn.commit()
                    print(f"  ✅ Added workspaces.{col}")
                except Exception as e:
                    print(f"  ⚠️  workspaces.{col}: {e}")

        # ── workspace_members table ───────────────────
        mem_cols = {c["name"] for c in insp.get_columns("workspace_members")}
        if "joined_at" not in mem_cols:
            try:
                conn.execute(text("ALTER TABLE workspace_members ADD COLUMN joined_at VARCHAR(64)"))
                conn.commit()
                print("  ✅ Added workspace_members.joined_at")
            except Exception as e:
                print(f"  ⚠️  workspace_members.joined_at: {e}")

        # ── invitations table ─────────────────────────
        inv_cols = {c["name"] for c in insp.get_columns("invitations")}
        if "invited_by" not in inv_cols:
            try:
                conn.execute(text("ALTER TABLE invitations ADD COLUMN invited_by VARCHAR(255)"))
                conn.commit()
                print("  ✅ Added invitations.invited_by")
            except Exception as e:
                print(f"  ⚠️  invitations.invited_by: {e}")

    print("✅ Migrations complete")

try:
    migrate()
except Exception as e:
    print(f"⚠️  Migration warning (non-fatal): {e}")

# ═══════════════════════════════════════════════════════
# STEP 3 — Seed admin account
# ═══════════════════════════════════════════════════════
step("Seeding admin account")
from app.models.user import User
from app.services.auth_service import get_user, create_user
from app.core.security import hash_password

admin_email    = os.getenv("ADMIN_EMAIL", "admin@cognidata.ai")
admin_password = os.getenv("ADMIN_PASSWORD", "adminrudra@1234")

db = SessionLocal()
try:
    existing = get_user(db, admin_email)
    if existing:
        # Ensure admin role + correct password
        existing.role   = "admin"
        existing.active = True
        existing.hashed_password = hash_password(admin_password)
        if not existing.created_at:
            existing.created_at = datetime.now(timezone.utc).isoformat()
        db.commit()
        print(f"✅ Admin account updated: {admin_email}")
    else:
        u = create_user(db, admin_email, admin_password)
        u.role   = "admin"
        u.active = True
        u.created_at = datetime.now(timezone.utc).isoformat()
        db.commit()
        print(f"✅ Admin account created: {admin_email}")

    total_users = db.query(User).count()
    print(f"   Total users in DB: {total_users}")
finally:
    db.close()

# ═══════════════════════════════════════════════════════
# STEP 4 — Seed default workspace for admin
# ═══════════════════════════════════════════════════════
step("Seeding default workspace")
from app.models.workspace import Workspace, WorkspaceMember

db = SessionLocal()
try:
    admin_user = get_user(db, admin_email)
    existing_ws = db.query(Workspace).filter(Workspace.owner_id == admin_user.id).first()
    if not existing_ws:
        now = datetime.now(timezone.utc).isoformat()
        ws = Workspace(
            name="Default Workspace",
            description="Your primary analytics workspace",
            owner_id=admin_user.id,
            created_at=now,
        )
        db.add(ws)
        db.flush()
        member = WorkspaceMember(workspace_id=ws.id, user_id=admin_user.id, role="admin")
        db.add(member)
        db.commit()
        print(f"✅ Default workspace created (id={ws.id})")
    else:
        print(f"✅ Workspace already exists: '{existing_ws.name}' (id={existing_ws.id})")
        # Ensure admin is a member
        mem = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == existing_ws.id,
            WorkspaceMember.user_id == admin_user.id
        ).first()
        if not mem:
            member = WorkspaceMember(workspace_id=existing_ws.id, user_id=admin_user.id, role="admin")
            db.add(member)
            db.commit()
            print("  ✅ Admin added as workspace member")
finally:
    db.close()

# ═══════════════════════════════════════════════════════
# STEP 5 — Configure SQLite pragmas (WAL + performance)
# ═══════════════════════════════════════════════════════
step("Applying SQLite performance settings")
if "sqlite" in DATABASE_URL:
    db_file = DATABASE_URL.replace("sqlite:///./", "")
    db_abs  = str(pathlib.Path(__file__).parent / db_file)
    conn = sqlite3.connect(db_abs)
    pragmas = [
        ("journal_mode", "WAL"),
        ("synchronous",  "NORMAL"),
        ("cache_size",   "-64000"),   # 64MB cache
        ("temp_store",   "MEMORY"),
        ("mmap_size",    "268435456"), # 256MB mmap
        ("foreign_keys", "ON"),
        ("auto_vacuum",  "INCREMENTAL"),
    ]
    for k, v in pragmas:
        conn.execute(f"PRAGMA {k}={v}")
        result = conn.execute(f"PRAGMA {k}").fetchone()[0]
        print(f"  {k} = {result}")
    conn.commit()
    conn.close()
    print("✅ SQLite optimized")
else:
    print("  (Skipped — using MySQL)")

# ═══════════════════════════════════════════════════════
# STEP 6 — Create data store directory
# ═══════════════════════════════════════════════════════
step("Setting up dataset store")
store_dir = pathlib.Path(__file__).parent / ".dataset_store"
store_dir.mkdir(exist_ok=True)
gitignore = store_dir / ".gitignore"
if not gitignore.exists():
    gitignore.write_text("*\n!.gitignore\n")
print(f"✅ Dataset store: {store_dir}")

# ═══════════════════════════════════════════════════════
# STEP 7 — Verify database integrity
# ═══════════════════════════════════════════════════════
step("Verifying database integrity")
if "sqlite" in DATABASE_URL:
    db_file = DATABASE_URL.replace("sqlite:///./", "")
    db_abs  = str(pathlib.Path(__file__).parent / db_file)
    conn = sqlite3.connect(db_abs)

    # Integrity check
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"  Integrity check: {result}")

    # Table summary
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    print(f"\n  {'Table':<25} {'Rows':>6}  Columns")
    print(f"  {'─'*50}")
    for (tname,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
        cols  = [c[1] for c in conn.execute(f"PRAGMA table_info({tname})").fetchall()]
        print(f"  {tname:<25} {count:>6}  {', '.join(cols)}")

    # DB file size
    size_kb = os.path.getsize(db_abs) / 1024
    print(f"\n  DB file: {db_abs}")
    print(f"  DB size: {size_kb:.1f} KB")
    conn.close()

# ═══════════════════════════════════════════════════════
# STEP 8 — Test SMTP connection
# ═══════════════════════════════════════════════════════
step("Testing SMTP connection")
smtp_enabled = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
smtp_user    = os.getenv("SMTP_USER", "")
smtp_pass    = os.getenv("SMTP_PASSWORD", "")
smtp_host    = os.getenv("SMTP_HOST", "smtp.gmail.com")
smtp_port    = int(os.getenv("SMTP_PORT", "587"))

if smtp_enabled and smtp_user and smtp_pass:
    import smtplib
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(smtp_user, smtp_pass)
        print(f"✅ SMTP connected: {smtp_host}:{smtp_port} as {smtp_user}")
    except Exception as e:
        print(f"⚠️  SMTP test failed: {e}")
else:
    print("  ⏭  SMTP skipped (disabled or credentials not set)")

# ═══════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════
print(f"\n{'═'*55}")
print("  ✅  COGNIDATA DATABASE SETUP COMPLETE")
print(f"{'═'*55}")
print(f"\n  Admin login: {admin_email}")
print( "  Password:    (set in .env → ADMIN_PASSWORD)")
print( "  Backend:     http://localhost:8000")
print( "  Frontend:    http://localhost:5173")
print()
