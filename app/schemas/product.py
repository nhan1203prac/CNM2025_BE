from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = 0
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    main_image: Optional[str] = None
    is_new: Optional[bool] = False

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    rating_avg: Optional[Decimal] = 0
    reviews_count: Optional[int] = 0
    sold_count: Optional[int] = 0

    class Config:
        from_attributes = True