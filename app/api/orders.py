from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import uuid
from app.db.session import get_db
from app.models.order import Order, ShippingStatus 
from app.models.order_item import OrderItem
from app.models.cart_item import CartItem
from app.models.product import Product
from app.schemas.order import OrderResponse 
from app.api.deps import get_current_user
from typing import List

router = APIRouter(prefix="/orders", tags=["Orders"])

# POST /orders/checkout
@router.post("/create", status_code=201)
def createOrder(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) 
):
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(status_code=400, detail="Giỏ hàng trống")

    total_amount = 0
    
    order = Order(
        user_id=current_user.id,
        total_amount=0,
        shipping_status="PENDING"
    )

    db.add(order)
    db.flush() 

    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            continue
        
        if product.stock < item.quantity:
            db.rollback() 
            raise HTTPException(
                status_code=400, 
                detail=f"Sản phẩm {product.name} không đủ số lượng trong kho"
            )

        product.stock -= item.quantity
        total_amount += product.price * item.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price_at_purchase=product.price,
            selected_size=getattr(item, 'selectedSize', None), 
            selected_color=getattr(item, 'selectedColor', None) 
        )

        db.add(order_item)
        db.delete(item) 

    order.total_amount = total_amount
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "total_amount": float(order.total_amount),
        "status": order.shipping_status
    }

# GET /orders
@router.get("", response_model=List[OrderResponse]) 
def get_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    orders = (
        db.query(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product)
        )
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

# GET /orders/{order_id}
@router.get("/{order_id}", response_model=OrderResponse)
def get_order_detail(
    order_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product)
        )
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id 
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại")

    return order

# PUT /orders/{order_id}/status (Cho khách hàng Hủy đơn)
@router.put("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == order_id, 
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại")
    
    if order.shipping_status != "PENDING":
        raise HTTPException(status_code=400, detail="Chỉ có thể hủy đơn hàng đang chờ xử lý")

    order.shipping_status = "CANCELLED"
    db.commit()
    
    return {"message": "Đã hủy đơn hàng thành công"}