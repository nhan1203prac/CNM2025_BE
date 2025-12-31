from datetime import date
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

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None

class ProfileResponse(BaseModel):
    id: int
    full_name: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    
    # d├▓ng n├áy gi├║p ─æß╗ìc dß╗» liß╗çu tß╗½ ORM model ß╗ƒ dß║íng object v├¡ dß╗Ñ User.profile.full_name
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
    token_type: str = "bearer"
    isActive: bool
    user: UserResponse

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class VerifyCodeRequest(BaseModel):
    verification_code: str
    
