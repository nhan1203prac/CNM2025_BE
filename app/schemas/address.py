from pydantic import BaseModel
from typing import Optional

class AddressBase(BaseModel):
    receiver_name: str
    receiver_phone: str
    
    province: str
    district: str
    ward: str
    
    province_id: int
    district_id: int
    ward_code: str
    
    street_details: str
    type: str = "Nhà riêng" 
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel): 
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    province: Optional[str] = None
    province_id: Optional[int] = None
    district: Optional[str] = None
    district_id: Optional[int] = None
    ward: Optional[str] = None
    ward_code: Optional[str] = None
    street_details: Optional[str] = None
    type: Optional[str] = None
    is_default: Optional[bool] = None

class AddressResponse(AddressBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True