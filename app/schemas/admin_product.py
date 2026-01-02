from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class ProductImageSchema(BaseModel):
    image_url: str

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = 0
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    stock: int = 0
    main_image: Optional[str] = None
    is_new: Optional[bool] = False

class ProductCreate(ProductBase):
    images: Optional[List[str]] = []

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = None
    category_id: Optional[int] = None
    stock: Optional[int] = None
    main_image: Optional[str] = None
    is_new: Optional[bool] = None
    images: Optional[List[str]] = None

class ProductAdminResponse(ProductBase):
    id: int
    category_name: Optional[str] = None
    images: List[str] = [] 

    class Config:
        from_attributes = True