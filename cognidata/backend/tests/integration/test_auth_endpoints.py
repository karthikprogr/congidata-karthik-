"""
Integration tests for authentication endpoints.
Tests Requirements 11.1, 11.2, 17.1, 17.2
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import decode_token


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create test client and fresh database for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield TestClient(app)
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


class TestRegisterEndpoint:
    """Test user registration endpoint."""
    
    def test_register_new_user_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={"email": "newuser@example.com", "password": "secure_pass123"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Account created"
        assert "user_id" in data
        assert data["tier"] == "free"
        assert data["storage_quota_mb"] == 100
    
    def test_register_duplicate_email_fails(self, client):
        """Test that registering duplicate email returns 400."""
        # Register first user
        client.post(
            "/auth/register",
            json={"email": "duplicate@example.com", "password": "password1"}
        )
        
        # Try to register again with same email
        response = client.post(
            "/auth/register",
            json={"email": "duplicate@example.com", "password": "password2"}
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_first_user_becomes_admin(self, client):
        """Test that first registered user gets admin role."""
        # Register first user
        response = client.post(
            "/auth/register",
            json={"email": "admin@example.com", "password": "admin_pass"}
        )
        
        assert response.status_code == 201
        
        # Login to get token
        login_response = client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "admin_pass"}
        )
        
        token = login_response.json()["access_token"]
        payload = decode_token(token)
        
        # First user should be admin
        assert payload["role"] == "admin"


class TestLoginEndpoint:
    """Test user login endpoint."""
    
    def test_login_with_valid_credentials(self, client):
        """Test successful login with valid credentials."""
        # Register user
        client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "my_password"}
        )
        
        # Login
        response = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "my_password"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token contains user info
        token = data["access_token"]
        payload = decode_token(token)
        assert payload["email"] == "user@example.com"
        assert payload["sub"] == "user@example.com"
        assert "user_id" in payload
        assert "tier" in payload
        assert "role" in payload
    
    def test_login_with_invalid_password(self, client):
        """Test login fails with incorrect password."""
        # Register user
        client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "correct_password"}
        )
        
        # Try login with wrong password
        response = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrong_password"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_with_nonexistent_email(self, client):
        """Test login fails with non-existent email."""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "any_password"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_token_includes_tier_information(self, client):
        """Test that login token includes tier and storage quota info."""
        # Register user (gets 'free' tier by default)
        client.post(
            "/auth/register",
            json={"email": "free_user@example.com", "password": "password"}
        )
        
        # Login
        response = client.post(
            "/auth/login",
            json={"email": "free_user@example.com", "password": "password"}
        )
        
        token = response.json()["access_token"]
        payload = decode_token(token)
        
        assert payload["tier"] == "free"
        assert payload["user_id"] is not None


class TestAuthenticationMiddleware:
    """Test authentication middleware for protected routes."""
    
    def test_protected_route_without_token_fails(self, client):
        """Test accessing protected route without token returns 403."""
        response = client.post("/auth/logout")
        
        # Should fail because no Authorization header
        assert response.status_code == 403
    
    def test_protected_route_with_valid_token_succeeds(self, client):
        """Test accessing protected route with valid token succeeds."""
        # Register and login
        client.post(
            "/auth/register",
            json={"email": "protected@example.com", "password": "password"}
        )
        login_response = client.post(
            "/auth/login",
            json={"email": "protected@example.com", "password": "password"}
        )
        
        token = login_response.json()["access_token"]
        
        # Access protected route
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_protected_route_with_invalid_token_fails(self, client):
        """Test accessing protected route with invalid token fails."""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401


class TestTokenExpiration:
    """Test JWT token expiration handling."""
    
    def test_token_contains_expiration(self, client):
        """Test that generated tokens include expiration timestamp."""
        # Register and login
        client.post(
            "/auth/register",
            json={"email": "exp_test@example.com", "password": "password"}
        )
        login_response = client.post(
            "/auth/login",
            json={"email": "exp_test@example.com", "password": "password"}
        )
        
        token = login_response.json()["access_token"]
        payload = decode_token(token)
        
        # Token should have 'exp' claim
        assert "exp" in payload
        assert isinstance(payload["exp"], int)
        
        # Expiration should be in the future
        from datetime import datetime, timezone
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert exp_time > now


class TestUserTierInToken:
    """Test that user tier is properly included in tokens."""
    
    def test_new_user_has_free_tier(self, client):
        """Test that newly registered users get 'free' tier."""
        # Register
        reg_response = client.post(
            "/auth/register",
            json={"email": "freetier@example.com", "password": "password"}
        )
        
        assert reg_response.json()["tier"] == "free"
        
        # Login and verify token
        login_response = client.post(
            "/auth/login",
            json={"email": "freetier@example.com", "password": "password"}
        )
        
        token = login_response.json()["access_token"]
        payload = decode_token(token)
        
        assert payload["tier"] == "free"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
