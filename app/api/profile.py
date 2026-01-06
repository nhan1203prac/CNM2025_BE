from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import Any
from app.db.session import get_db
from app.models.order import Order, ShippingStatus
from app.models.product import Product
from app.models.favorite import Favorite
from app.models.user import User
from app.models.order_item import OrderItem
from app.api.deps import get_current_user
from app.api import deps
from app.schemas.profile import DashboardResponse

router = APIRouter()

@router.get("/", response_model = DashboardResponse)
def get_dashboard_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),

) -> Any:
    processing_count = db.query(Order).filter(
        Order.user_id == current_user.id, 
        Order.shipping_status == ShippingStatus.PENDING
    ).count()
    
    completed_count = db.query(Order).filter(
        Order.user_id == current_user.id, 
        Order.shipping_status == ShippingStatus.DELIVERED
    ).count()

  
    wishlist_items = db.query(Product).join(Favorite).filter(
        Favorite.user_id == current_user.id
    ).limit(4).all()

    recent_orders_raw = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).limit(5).all()

    recent_orders = []
    for order in recent_orders_raw:
        first_item = order.items[0].product.name if order.items else "Không có sản phẩm"

        items_count = len(order.items)
        

        recent_orders.append({
            "id": order.id,
            "date": order.created_at,
            "first_item_name": first_item,
            "total": order.total_amount,
            "status": order.shipping_status.value,
            "items_count": items_count
        })
    
    return {
        "stats": {
            "processing_orders": processing_count,
            "completed_orders": completed_count,
            "wishlist_count": len(wishlist_items)
        },
        "recent_orders": recent_orders,
        "wishlist": wishlist_items
    }