from fastapi import (
    APIRouter, HTTPException, Depends, Query, Request
)
from sqlalchemy.orm import Session
import stripe
import os

from app.db.session import get_db
from app.models.order import Order

router = APIRouter(prefix="/payment", tags=["Payment"])

# Stripe API Key từ .env
stripe.api_key = os.getenv("STRIPE_API_KEY")  # test key

# HARDCODE USER
TEST_USER_ID = 1

# POST /payment/create-session
# Tạo Stripe Checkout session
@router.post("/create-session/{order_id}")
def create_checkout_session(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == TEST_USER_ID).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    # Tạo line_items cho Stripe
    line_items = [{
        "price_data": {
            "currency": "usd",
            "product_data": {
                "name": f"Order {order.id}"
            },
            "unit_amount": int(order.total_amount * 100),
        },
        "quantity": 1
    }]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"http://localhost:3000/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"http://localhost:3000/payment-cancel",
            metadata={"order_id": order.id}
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# POST /payment/confirm
@router.post("/confirm")
def confirm_payment(
    session_id: str = Query(...),
    db: Session = Depends(get_db)
):
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Thanh toán chưa hoàn tất")

    order_id = session.metadata.get("order_id")
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    order.status = "Đã thanh toán"
    db.commit()

    return {
        "status": "success",
        "order_id": order.id,
        "total_amount_vnd": order.total_amount
    }

