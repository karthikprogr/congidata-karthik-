"""
Security utilities for JWT token generation and password hashing.
Implements Requirements 11.1, 11.2, 17.1, 17.2
"""
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import jwt, JWTError
from app.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_HOURS

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd.verify(plain_password, hashed_password)


def create_token(data: dict, expire_minutes: Optional[int] = None) -> str:
    """
    Create a JWT token with user information.
    
    JWT tokens include: user_id, email, tier, role, exp (24h expiration)
    Validates Requirement 17.1, 17.2
    
    Args:
        data: Token payload containing user info (user_id, email, tier, role)
        expire_minutes: Optional custom expiration in minutes (default: 24 hours)
        
    Returns:
        Encoded JWT token string
    """
    if expire_minutes is not None:
        delta = timedelta(minutes=expire_minutes)
    else:
        delta = timedelta(hours=TOKEN_EXPIRE_HOURS)
    
    payload = {
        **data,
        "exp": datetime.now(timezone.utc) + delta
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.
    
    Validates signature and expiration (Requirement 17.1)
    Raises JWTError if token is invalid or expired
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload dictionary
        
    Raises:
        JWTError: If token is invalid, expired, or signature verification fails
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation failed: {str(e)}")
