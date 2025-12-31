import hashlib
import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def _prepare_password(password: str) -> bytes:
    """Chuẩn bị mật khẩu cho bcrypt (tối đa 72 byte)"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Hash SHA256 trước nếu vượt 72 byte
        return hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    return password_bytes

def hash_password(password: str) -> str:
    prepared = _prepare_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    prepared = _prepare_password(password)
    return bcrypt.checkpw(prepared, hashed_password.encode('utf-8'))

def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': str(subject), # 'sub' là field tiêu chuẩn trong JWT
        'exp': expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def is_token_expired(token: str) -> bool:
    """Kiểm tra token có hết hạn không"""
    try:
        payload = decode_access_token(token)
        exp = payload.get("exp")
        return datetime.utcnow().timestamp() > exp
    except:
        return True

def get_token_from_header(authorization: str = Header(None, alias="Authorization", include_in_schema=False)) -> str:
    """Lấy token từ Authorization header"""
    logger.info(f"Authorization header: {authorization}")
    
    if not authorization:
        logger.error("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Xử lý cả hai format: "Bearer <token>" và chỉ "<token>"
    parts = authorization.split()
    
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    elif len(parts) == 1:
        # Token được gửi trực tiếp từ Swagger (không có "Bearer")
        token = parts[0]
    else:
        logger.error(f"Invalid Authorization format: {authorization}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Token extracted: {token[:20]}...")
    return token

def get_current_user_from_token(token: str = Depends(get_token_from_header)) -> str:
    """
    Lấy email từ token JWT.
    Được sử dụng làm dependency injection.
    Returns email từ token.
    """
    try:
        logger.info("Decoding token...")
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        
        if email is None:
            logger.error("Token missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Token decoded successfully, email: {email}")
        return email
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
