"""
Authentication service for user management.
Implements user creation, authentication, and tier management.
"""
import secrets
from typing import Optional
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.utils.auth import get_tier_quota, validate_tier


def get_user(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by email.
    
    Args:
        db: Database session
        email: User email address
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieve a user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password: str, tier: str = "free") -> User:
    """
    Create a new user with hashed password and tier.
    
    First user automatically becomes admin.
    Sets storage quota based on tier.
    
    Args:
        db: Database session
        email: User email address
        password: Plain text password (will be hashed)
        tier: Subscription tier (default: 'free')
        
    Returns:
        Created User object
    """
    # First user becomes admin
    role = "admin" if db.query(User).count() == 0 else "user"
    
    # Validate and set tier
    if not validate_tier(tier):
        tier = "free"
    
    storage_quota = get_tier_quota(tier)
    
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role,
        tier=tier,
        storage_quota_mb=storage_quota
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session
        email: User email address
        password: Plain text password
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = get_user(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_or_create_oauth_user(db: Session, email: str, tier: str = "free") -> User:
    """
    Get existing OAuth user or create new one.
    
    OAuth users get a random password they cannot use directly.
    
    Args:
        db: Database session
        email: User email from OAuth provider
        tier: Initial tier for new users (default: 'free')
        
    Returns:
        User object
    """
    user = get_user(db, email)
    if not user:
        # Create with random password (OAuth users don't use password auth)
        user = create_user(db, email, secrets.token_hex(32), tier=tier)
    return user


def update_user_tier(db: Session, user_id: int, new_tier: str) -> Optional[User]:
    """
    Update a user's subscription tier and storage quota.
    
    Args:
        db: Database session
        user_id: User ID
        new_tier: New subscription tier
        
    Returns:
        Updated User object if found, None otherwise
    """
    if not validate_tier(new_tier):
        raise ValueError(f"Invalid tier: {new_tier}")
    
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.tier = new_tier
    user.storage_quota_mb = get_tier_quota(new_tier)
    
    db.commit()
    db.refresh(user)
    
    return user
