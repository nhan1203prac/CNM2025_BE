from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    image_url: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    class Config:
        from_attributes = True