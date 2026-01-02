from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class RevenueData(BaseModel):
    date: str
    amount: float

class CategoryShare(BaseModel):
    name: str
    value: int

class DashboardResponse(BaseModel):
    stats: List[Dict[str, Any]]
    revenue_chart: List[RevenueData]
    top_categories: List[CategoryShare]
    recent_orders: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)