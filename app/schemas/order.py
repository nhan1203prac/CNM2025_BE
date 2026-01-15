from pydantic import BaseModel, ConfigDict 
from typing import List, Optional
from datetime import datetime

class ProductInOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    main_image: Optional[str]

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quantity: int
    price_at_purchase: float
    selected_size: Optional[str]
    selected_color: Optional[str]
    product: Optional[ProductInOrder] = None 

class OrderCreateRequest(BaseModel):
    address_id: int

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    total_amount: float
    shipping_status: str
    payment_status: str
    created_at: datetime
    shipping_fee: float
    expected_delivery_date: Optional[str] = None 
    delivery_deadline: Optional[str] = None
    tracking_code: Optional[str] = None # mã vận đơn 
    items: List[OrderItemResponse] = [] 