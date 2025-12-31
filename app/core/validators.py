"""
Validation functions for user input validation
"""
from fastapi import HTTPException, status


def validate_email(email: str) -> None:
    """
    Validate email format.
    
    Args:
        email: Email string to validate
        
    Raises:
        HTTPException: If email format is invalid
    """
    if "@" not in email or "." not in email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email không hợp lệ"
        )


def validate_password(password: str) -> None:
    """
    Validate password strength.
    
    Args:
        password: Password string to validate
        
    Raises:
        HTTPException: If password is too weak
    """
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mật khẩu phải có ít nhất 6 ký tự"
        )


def validate_username(username: str) -> None:
    """
    Validate username format.
    
    Args:
        username: Username string to validate
        
    Raises:
        HTTPException: If username format is invalid
    """
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tên tài khoản phải có ít nhất 3 ký tự"
        )
    
    if len(username) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tên tài khoản không được vượt quá 100 ký tự"
        )
