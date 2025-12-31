from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.db.session import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.cart_item import CartItem
from app.models.product import Product

router = APIRouter(prefix="/orders", tags=["Orders"])

# USER CỐ ĐỊNH ĐỂ TEST
TEST_USER_ID = 1

# POST /orders/checkout
# Tạo đơn hàng từ giỏ hàng
@router.post("/checkout", status_code=201)
def checkout(db: Session = Depends(get_db)):
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == TEST_USER_ID)
        .all()
    )

    if not cart_items:
        raise HTTPException(status_code=400, detail="Giỏ hàng trống")

    order_id = str(uuid.uuid4())
    total_amount = 0

    order = Order(
        id=order_id,
        user_id=TEST_USER_ID,
        total_amount=0,
        status="Chờ xử lý"
    )

    db.add(order)
    db.flush() 

    for item in cart_items:
        product = db.query(Product).get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

        total_amount += product.price * item.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price_at_purchase=product.price
        )

        db.add(order_item)
        db.delete(item) 

    order.total_amount = total_amount
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "total_amount": float(order.total_amount),
        "status": order.status
    }

# GET /orders
# Lấy lịch sử đơn hàng
@router.get("")
def get_orders(db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.user_id == TEST_USER_ID)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

# GET /orders/{order_id}
# Xem chi tiết đơn hàng
@router.get("/{order_id}")
def get_order_detail(order_id: str, db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == TEST_USER_ID
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại")

    return order

# PUT /orders/{order_id}/status
# Cập nhật trạng thái đơn hàng (giả admin)
@router.put("/{order_id}/status")
def update_order_status(
    order_id: str,
    new_status: str,
    db: Session = Depends(get_db)
):
    allowed_status = ["Chờ xử lý", "Đang vận chuyển", "Đã giao"]

    if new_status not in allowed_status:
        raise HTTPException(
            status_code=400,
            detail=f"Trạng thái phải là một trong: {allowed_status}"
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại")

    order.status = new_status
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "status": order.status
    }
