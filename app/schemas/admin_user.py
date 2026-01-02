from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

class ProfileSchema(BaseModel):
    full_name: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None

class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: str
    isAdmin: bool
    is_active: bool
    created_at: datetime
    profile: Optional[ProfileSchema]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    isAdmin: Optional[bool] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    avatar: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  
    isAdmin: Optional[bool] = False
    is_active: Optional[bool] = True
    full_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = "Nam"
    avatar: Optional[str] = None