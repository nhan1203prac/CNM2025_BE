from pydantic import BaseModel, EmailStr
from typing import Optional

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str

class ProfileResponse(BaseModel):
    id: int
    full_name: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    
    # dòng này giúp đọc dữ liệu từ ORM model ở dạng object ví dụ User.profile.full_name
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    isAdmin: bool
    profile: Optional[ProfileResponse] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    isActive: bool
    user: UserResponse