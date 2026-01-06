from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.product import ProductResponse

class DashboardStats(BaseModel):
    processing_orders: int
    completed_orders: int
    wishlist_count: int



class RecentOrder(BaseModel):
    id: int
    date: datetime
    first_item_name: str
    total: float
    status: str
    items_count: int

class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_orders: List[RecentOrder]
    wishlist: List[ProductResponse]
