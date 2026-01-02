from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.admin_user import UserAdminResponse, UserUpdate, UserCreate
from app.api.deps import get_current_active_admin
from app.core.security import hash_password
from typing import List
from typing import Optional
router = APIRouter()

@router.get("", response_model=List[UserAdminResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin),
    search: Optional[str] = Query(None),    
    is_admin: Optional[bool] = Query(None)
):
    query = db.query(User).options(joinedload(User.profile)).join(Profile)
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | 
            (User.email.ilike(f"%{search}%")) |
            (Profile.full_name.ilike(f"%{search}%"))
        )
    if is_admin is not None:
        query = query.filter(User.isAdmin == is_admin)

    users = query.order_by(User.id.desc()).all()
    return users


@router.post("", response_model=UserAdminResponse)
def create_user_system(
    obj_in: UserCreate, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    user_exists = db.query(User).filter(
        (User.username == obj_in.username) | (User.email == obj_in.email)
    ).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username hoặc Email đã tồn tại")

    new_profile = Profile(
        full_name=obj_in.full_name,
        phone=obj_in.phone,
        gender=obj_in.gender,
        avatar=obj_in.avatar
    )
    db.add(new_profile)
    db.flush() 

    new_user = User(
        username=obj_in.username,
        email=obj_in.email,
        password=hash_password(obj_in.password), 
        isAdmin=obj_in.isAdmin,
        is_active=obj_in.is_active,
        profile_id=new_profile.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.patch("/{user_id}")
def update_user_system(
    user_id: int, 
    obj_in: UserUpdate, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    user_data = obj_in.model_dump(include={"email", "isAdmin", "is_active"}, exclude_unset=True)
    for field in user_data:
        setattr(db_user, field, user_data[field])

    if db_user.profile:
        profile_data = obj_in.model_dump(
            include={"full_name", "phone", "gender", "avatar"}, 
            exclude_unset=True
        )
        for field in profile_data:
            setattr(db_user.profile, field, profile_data[field])
    
    db.commit()
    return {"message": "Cập nhật thành công"}

@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(404, "Không tìm thấy người dùng")
    
    db.delete(db_user)
    db.commit()
    return {"message": "Đã xóa người dùng"}