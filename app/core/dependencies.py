"""
Database dependencies and query functions for FastAPI dependency injection
"""
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging
from typing import Optional
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_user_from_token, decode_access_token


logger = logging.getLogger(__name__)


def get_current_user(
    email: str = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current User object from token.
    
    Args:
        email: User email extracted from JWT token
        db: Database session
        
    Returns:
        User: The user object from database
        
    Raises:
        HTTPException: If user not found
    """
    logger.info(f"Looking up user with email: {email}")
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.error(f"User not found: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    logger.info(f"User found: {user.username}")
    return user



