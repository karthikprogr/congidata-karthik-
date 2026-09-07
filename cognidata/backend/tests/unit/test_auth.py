"""
Unit tests for authentication system.
Tests Requirements 11.1, 11.2, 17.1, 17.2
"""
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.security import hash_password, verify_password, create_token, decode_token
from app.utils.auth import (
    create_user_token,
    validate_tier,
    get_tier_quota,
    get_tier_token_limit,
    extract_user_from_token,
    TIER_CONFIG
)
from app.core.config import SECRET_KEY, ALGORITHM


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_creates_valid_hash(self):
        """Test that password hashing creates a bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length
    
    def test_verify_password_with_correct_password(self):
        """Test password verification succeeds with correct password."""
        password = "secure_password_456"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_with_incorrect_password(self):
        """Test password verification fails with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token generation and validation."""
    
    def test_create_token_with_default_expiration(self):
        """Test creating token with default 24h expiration."""
        data = {"user_id": 1, "sub": "test@example.com", "tier": "free"}
        token = create_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == 1
        assert payload["sub"] == "test@example.com"
        assert payload["tier"] == "free"
        assert "exp" in payload
    
    def test_create_token_with_custom_expiration(self):
        """Test creating token with custom expiration time."""
        data = {"user_id": 2, "sub": "user@example.com"}
        token = create_token(data, expire_minutes=10)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should expire in approximately 10 minutes
        time_diff = exp_time - now
        assert 9.5 * 60 < time_diff.total_seconds() < 10.5 * 60
    
    def test_decode_valid_token(self):
        """Test decoding a valid JWT token."""
        data = {
            "user_id": 3,
            "sub": "valid@example.com",
            "tier": "pro",
            "role": "user"
        }
        token = create_token(data)
        
        decoded = decode_token(token)
        assert decoded["user_id"] == 3
        assert decoded["sub"] == "valid@example.com"
        assert decoded["tier"] == "pro"
        assert decoded["role"] == "user"
    
    def test_decode_expired_token_raises_error(self):
        """Test that decoding expired token raises JWTError."""
        data = {"user_id": 4, "sub": "expired@example.com"}
        
        # Create token that expired 1 hour ago
        payload = {
            **data,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(JWTError):
            decode_token(expired_token)
    
    def test_decode_invalid_signature_raises_error(self):
        """Test that decoding token with invalid signature raises JWTError."""
        data = {"user_id": 5, "sub": "invalid@example.com"}
        token = create_token(data)
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered00"
        
        with pytest.raises(JWTError):
            decode_token(tampered_token)


class TestUserToken:
    """Test user-specific token creation."""
    
    def test_create_user_token_with_all_fields(self):
        """Test creating user token with user_id, email, tier, role."""
        token = create_user_token(
            user_id=10,
            email="user@example.com",
            tier="basic",
            role="user"
        )
        
        payload = decode_token(token)
        assert payload["user_id"] == 10
        assert payload["email"] == "user@example.com"
        assert payload["sub"] == "user@example.com"  # Standard JWT claim
        assert payload["tier"] == "basic"
        assert payload["role"] == "user"
    
    def test_create_user_token_admin(self):
        """Test creating admin user token."""
        token = create_user_token(
            user_id=1,
            email="admin@example.com",
            tier="pro",
            role="admin"
        )
        
        payload = decode_token(token)
        assert payload["role"] == "admin"
        assert payload["tier"] == "pro"
    
    def test_extract_user_from_token(self):
        """Test extracting user info from decoded token payload."""
        payload = {
            "user_id": 20,
            "sub": "extract@example.com",
            "tier": "free",
            "role": "user",
            "exp": 1234567890
        }
        
        user_info = extract_user_from_token(payload)
        assert user_info["user_id"] == 20
        assert user_info["email"] == "extract@example.com"
        assert user_info["tier"] == "free"
        assert user_info["role"] == "user"


class TestTierValidation:
    """Test tier validation and configuration."""
    
    def test_validate_tier_free(self):
        """Test that 'free' is a valid tier."""
        assert validate_tier("free") is True
    
    def test_validate_tier_basic(self):
        """Test that 'basic' is a valid tier."""
        assert validate_tier("basic") is True
    
    def test_validate_tier_pro(self):
        """Test that 'pro' is a valid tier."""
        assert validate_tier("pro") is True
    
    def test_validate_tier_invalid(self):
        """Test that invalid tier names return False."""
        assert validate_tier("premium") is False
        assert validate_tier("enterprise") is False
        assert validate_tier("") is False
        assert validate_tier("FREE") is False  # Case sensitive
    
    def test_get_tier_quota_free(self):
        """Test storage quota for free tier."""
        quota = get_tier_quota("free")
        assert quota == 100  # 100MB
    
    def test_get_tier_quota_basic(self):
        """Test storage quota for basic tier."""
        quota = get_tier_quota("basic")
        assert quota == 1000  # 1GB
    
    def test_get_tier_quota_pro(self):
        """Test storage quota for pro tier."""
        quota = get_tier_quota("pro")
        assert quota == 10000  # 10GB
    
    def test_get_tier_quota_invalid_defaults_to_free(self):
        """Test that invalid tier returns free tier quota."""
        quota = get_tier_quota("invalid_tier")
        assert quota == 100  # Default to free
    
    def test_get_tier_token_limit_free(self):
        """Test daily token limit for free tier."""
        limit = get_tier_token_limit("free")
        assert limit == 10000
    
    def test_get_tier_token_limit_basic(self):
        """Test daily token limit for basic tier."""
        limit = get_tier_token_limit("basic")
        assert limit == 100000
    
    def test_get_tier_token_limit_pro(self):
        """Test daily token limit for pro tier."""
        limit = get_tier_token_limit("pro")
        assert limit == 1000000
    
    def test_tier_config_structure(self):
        """Test that TIER_CONFIG has expected structure."""
        assert "free" in TIER_CONFIG
        assert "basic" in TIER_CONFIG
        assert "pro" in TIER_CONFIG
        
        for tier_name, config in TIER_CONFIG.items():
            assert "storage_quota_mb" in config
            assert "daily_token_limit" in config
            assert "name" in config
            assert isinstance(config["storage_quota_mb"], int)
            assert isinstance(config["daily_token_limit"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
