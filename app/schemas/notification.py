from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class NotificationBase(BaseModel):
    title: str
    content: str
    type: str # order, promo, system
    is_read: bool = False

class NotificationResponse(NotificationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: bool