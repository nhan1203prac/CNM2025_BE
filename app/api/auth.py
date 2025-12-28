from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.userDto import UserCreate, UserLogin, Token
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user_exists = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    
    if user_exists:
        raise HTTPException(status_code=400, detail="Username hoặc Email đã tồn tại")

    new_profile = Profile(full_name=user_in.full_name)
    db.add(new_profile)
    db.flush()

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password=get_password_hash(user_in.password),
        profile_id=new_profile.id,
        is_active=False
    )
    db.add(new_user)
    
    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống")

    token = create_access_token(subject=new_user.email)

    return {
        "access_token": token,
        "isActive": new_user.is_active,
        "user": new_user
    }

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    
    if not user or not verify_password(user_in.password, user.password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")

    token = create_access_token(subject=user.email)

    return {
        "access_token": token,
        "isActive": user.is_active,
        "user": user
    }