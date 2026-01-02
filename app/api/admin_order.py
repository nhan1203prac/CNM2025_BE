from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, cast, String 
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.models.profile import Profile
from app.api.deps import get_current_active_admin
from app.schemas.admin_order import OrderPaginationResponse
from typing import Optional
import math

router = APIRouter()

@router.get("/orders", response_model=OrderPaginationResponse)
def get_admin_orders(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None 
):
    query = db.query(Order).join(User).outerjoin(Profile).options(
        joinedload(Order.user).joinedload(User.profile)
    )

    if search:
        query = query.filter(or_(
            cast(Order.id, String).ilike(f"%{search}%"),
            Profile.full_name.ilike(f"%{search}%"),
            User.username.ilike(f"%{search}%")
        ))

    if status:
        query = query.filter(Order.shipping_status == status.upper())

    total_count = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()

    formatted_items = []
    for o in orders:
        c_name = "Khách hàng"
        if o.user:
            c_name = o.user.profile.full_name if (o.user.profile and o.user.profile.full_name) else o.user.username

        formatted_items.append({
            "id": o.id,
            "customerName": c_name,
            "customerEmail": o.user.email if o.user else "N/A",
            "date": o.created_at.strftime("%d/%m/%Y %H:%M"),
            "total": float(o.total_amount),
            "paymentStatus": o.payment_status.value if hasattr(o.payment_status, 'value') else o.payment_status,
            "shippingStatus": o.shipping_status.value if hasattr(o.shipping_status, 'value') else o.shipping_status
        })

    return {
        "items": formatted_items,
        "total": total_count,
        "page": page,
        "size": size,
        "pages": math.ceil(total_count / size)
    }

@router.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không thấy đơn hàng")
    
    if "shippingStatus" in payload:
        order.shipping_status = payload["shippingStatus"].upper()
    if "paymentStatus" in payload:
        order.payment_status = payload["paymentStatus"].upper()
        
    db.commit()
    return {"message": "Cập nhật thành công"}