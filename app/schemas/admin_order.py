from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class OrderListItem(BaseModel):
    id: int
    customerName: str
    customerEmail: str
    date: str
    total: float
    paymentStatus: str
    shippingStatus: str

    model_config = ConfigDict(from_attributes=True)

class OrderPaginationResponse(BaseModel):
    items: List[OrderListItem]
    total: int
    page: int
    size: int
    pages: int