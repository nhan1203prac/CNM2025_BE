from pydantic import BaseModel
from typing import Optional

class AddressBase(BaseModel):
    receiver_name: str
    receiver_phone: str
    province: str
    district: str
    ward: str
    street_details: str
    type: str = "Nhà riêng" 
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    street_details: Optional[str] = None

class AddressResponse(AddressBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True