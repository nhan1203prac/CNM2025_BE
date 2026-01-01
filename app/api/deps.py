from fastapi import Depends, HTTPException, status, Request 
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã token
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.isAdmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user

# def get_current_user(db: Session = Depends(get_db)):
#     # HARD CODE USER ID = 1
#     user = db.query(User).filter(User.id == 1).first()

#     if not user:
#         raise Exception("Hardcoded user not found")

#     return user


def get_optional_current_user(
    request: Request, 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dành cho trang Home: 
    - Có token hợp lệ -> Trả về User (để hiện trái tim đỏ).
    - Không có token hoặc token sai -> Trả về None (khách vẫn xem được trang).
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]

    try:
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        
        if email is None:
            return None
            
        user = db.query(User).filter(User.email == email).first()
        return user
        
    except Exception:
        return None
