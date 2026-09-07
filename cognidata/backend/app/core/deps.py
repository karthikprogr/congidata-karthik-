"""
Authentication dependencies and middleware.
Implements Requirements 11.1, 11.2, 17.1, 17.2
"""
import os
from typing import Dict
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import decode_token
from app.core.config import OPENAI_API_KEY
from app.utils.auth import extract_user_from_token

_bearer = HTTPBearer()


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> Dict:
    """
    Authenticate user from JWT token in Authorization header.
    
    Validates:
    - Token signature (Requirement 11.1)
    - Token expiration (Requirement 17.1)
    - Extracts user_id, email, tier, role (Requirement 17.2)
    
    Args:
        creds: Bearer token credentials from Authorization header
        
    Returns:
        Dictionary with user_id, email, tier, role
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        payload = decode_token(creds.credentials)
        user_info = extract_user_from_token(payload)
        
        # Validate required fields exist
        if not user_info.get("user_id") or not user_info.get("email"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user information"
            )
        
        return user_info
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


def require_admin(user: Dict = Depends(get_current_user)) -> Dict:
    """
    Require admin role for endpoint access.
    
    Implements authorization check (Requirement 11.2)
    
    Args:
        user: Current user from get_current_user dependency
        
    Returns:
        User dictionary if admin
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def require_tier(minimum_tier: str):
    """
    Create a dependency that requires a minimum subscription tier.
    
    Implements user tier validation (Requirement 11.2)
    
    Args:
        minimum_tier: Minimum tier required ('free', 'basic', 'pro')
        
    Returns:
        Dependency function
    """
    tier_hierarchy = {"free": 0, "basic": 1, "pro": 2}
    
    def tier_checker(user: Dict = Depends(get_current_user)) -> Dict:
        user_tier = user.get("tier", "free")
        
        if tier_hierarchy.get(user_tier, 0) < tier_hierarchy.get(minimum_tier, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {minimum_tier} tier or higher"
            )
        
        return user
    
    return tier_checker


def get_api_key(x_api_key: str = Header(default="")) -> str:
    """
    Get OpenAI API key from header or environment.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        API key string
        
    Raises:
        HTTPException: 401 if no API key is available
    """
    key = x_api_key or OPENAI_API_KEY
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OpenAI API key required"
        )
    return key
