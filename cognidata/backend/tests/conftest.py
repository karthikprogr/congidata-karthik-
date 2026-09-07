"""Shared fixtures for all tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_cognidata.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_tables():
    """Wipe all rows between tests."""
    yield
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            try:
                db.execute(table.delete())
            except Exception:
                # Skip tables that don't exist
                pass
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    app.dependency_overrides[get_db] = override_get_db
    
    # Disable rate limiting in tests
    from app.core.limiter import limiter
    limiter.enabled = False
    
    with TestClient(app) as c:
        yield c
    
    # Re-enable rate limiting after tests
    limiter.enabled = True
    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_user(client, email="test@example.com", password="password123"):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def login_user(client, email="test@example.com", password="password123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_headers(client, email="test@example.com", password="password123"):
    register_user(client, email, password)
    r = login_user(client, email, password)
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
