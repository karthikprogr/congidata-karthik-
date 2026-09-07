"""
Authentication utilities for JWT token generation and user management.
Implements Requirements 11.1, 11.2, 17.1, 17.2
"""
from typing import Dict, Optional
from app.core.security import create_token, hash_password, verify_password


# Tier configuration matching Requirements 12, 16
TIER_CONFIG = {
    "free": {
        "storage_quota_mb": 100,
        "daily_token_limit": 10000,
        "name": "Free"
    },
    "basic": {
        "storage_quota_mb": 1000,  # 1GB
        "daily_token_limit": 100000,
        "name": "Basic"
    },
    "pro": {
        "storage_quota_mb": 10000,  # 10GB
        "daily_token_limit": 1000000,
        "name": "Pro"
    }
}


def create_user_token(user_id: int, email: str, tier: str, role: str = "user") -> str:
    """
    Create a JWT token for a user with tier information.
    
    Token includes: user_id, email, tier, role, exp (24h expiration)
    Implements Requirements 17.1, 17.2
    
    Args:
        user_id: User database ID
        email: User email address
        tier: User subscription tier ('free', 'basic', 'pro')
        role: User role (default: 'user', can be 'admin')
        
    Returns:
        JWT token string
    """
    token_data = {
        "user_id": user_id,
        "sub": email,  # Standard JWT claim for subject (email)
        "email": email,
        "tier": tier,
        "role": role
    }
    return create_token(token_data)


def validate_tier(tier: str) -> bool:
    """
    Validate that a tier value is valid.
    
    Args:
        tier: Tier string to validate
        
    Returns:
        True if tier is valid, False otherwise
    """
    return tier in TIER_CONFIG


def get_tier_quota(tier: str) -> int:
    """
    Get storage quota in MB for a given tier.
    
    Args:
        tier: User subscription tier
        
    Returns:
        Storage quota in megabytes
    """
    return TIER_CONFIG.get(tier, TIER_CONFIG["free"])["storage_quota_mb"]


def get_tier_token_limit(tier: str) -> int:
    """
    Get daily AI token limit for a given tier.
    
    Args:
        tier: User subscription tier
        
    Returns:
        Daily token limit
    """
    return TIER_CONFIG.get(tier, TIER_CONFIG["free"])["daily_token_limit"]


def hash_user_password(password: str) -> str:
    """
    Hash a user password using bcrypt.
    Wrapper around core.security.hash_password for convenience.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return hash_password(password)


def verify_user_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a user password against its hash.
    Wrapper around core.security.verify_password for convenience.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return verify_password(plain_password, hashed_password)


def extract_user_from_token(token_payload: Dict) -> Dict:
    """
    Extract user information from a decoded JWT token.
    
    Args:
        token_payload: Decoded JWT payload dictionary
        
    Returns:
        Dictionary with user_id, email, tier, role
    """
    return {
        "user_id": token_payload.get("user_id"),
        "email": token_payload.get("sub") or token_payload.get("email"),
        "tier": token_payload.get("tier", "free"),
        "role": token_payload.get("role", "user")
    }
