"""Tests for security utilities: hashing, JWT tokens."""
import pytest
import time
from app.core.security import hash_password, verify_password, create_token, decode_token
from jose import JWTError


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        h = hash_password("mysecret")
        assert h != "mysecret"

    def test_verify_correct_password(self):
        h = hash_password("correct")
        assert verify_password("correct", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("correct")
        assert verify_password("wrong", h) is False

    def test_same_password_different_hashes(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salt

    def test_empty_password_hashes(self):
        h = hash_password("")
        assert verify_password("", h) is True


class TestJWTTokens:
    def test_create_and_decode_token(self):
        token = create_token({"sub": "user@example.com", "role": "user"})
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "user"

    def test_expired_token_raises(self):
        token = create_token({"sub": "x@example.com"}, expire_minutes=-1)
        with pytest.raises(Exception):
            decode_token(token)

    def test_tampered_token_raises(self):
        token = create_token({"sub": "x@example.com"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            decode_token(tampered)

    def test_token_contains_expiry(self):
        token = create_token({"sub": "x@example.com"})
        payload = decode_token(token)
        assert "exp" in payload

    def test_2fa_pending_token(self):
        token = create_token({"sub": "x@example.com", "2fa_pending": True}, expire_minutes=5)
        payload = decode_token(token)
        assert payload.get("2fa_pending") is True

    def test_short_lived_token(self):
        token = create_token({"sub": "x@example.com"}, expire_minutes=1)
        payload = decode_token(token)
        assert payload["sub"] == "x@example.com"
