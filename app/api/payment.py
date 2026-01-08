from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import stripe

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.order import Order, PaymentStatus

router = APIRouter(prefix="/payment", tags=["Payment"])

# Cấu hình API Key một lần
stripe.api_key = settings.STRIPE_SECRET_KEY

def _to_cents(amount: Decimal) -> int:
    """Chuyển đổi tiền tệ sang đơn vị nhỏ nhất (cents/đồng) chính xác."""
    return int(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)

def _get_order(db: Session, order_id: int, user_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return order


@router.get("/status/{order_id}")
def get_payment_status(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = _get_order(db, order_id, user.id)
    return {
        "payment_status": order.payment_status.value if order.payment_status else None,
        "payment_intent_id": order.payment_intent_id,
        "total_amount": float(order.total_amount),
    }

@router.post("/intents/{order_id}")
def create_payment_intent(
    order_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    """
    API duy nhất để bắt đầu thanh toán. 
    Trả về client_secret để Frontend (Web/Mobile) tự xử lý form thẻ.
    """
    order = _get_order(db, order_id, user.id)

    if order.payment_status == PaymentStatus.PAID:
        return {"status": "already_paid", "payment_intent_id": order.payment_intent_id}

    # Tạo hoặc tái sử dụng PaymentIntent
    # Idempotency_key giúp tránh tạo trùng giao dịch nếu gọi API nhiều lần
    intent = stripe.PaymentIntent.create(
        amount=_to_cents(order.total_amount),
        currency=settings.STRIPE_CURRENCY,
        metadata={"order_id": order.id, "user_id": user.id},
        automatic_payment_methods={"enabled": True},
        idempotency_key=f"intent-order-{order.id}",
    )

    order.payment_intent_id = intent.id
    db.commit()

    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "status": intent.status,
    }

@router.post("/refund/{order_id}")
def refund_order(order_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Hoàn tiền đơn giản qua Payment Intent ID."""
    order = _get_order(db, order_id, user.id)
    if not order.payment_intent_id:
        raise HTTPException(400, "Đơn hàng này chưa được thanh toán qua hệ thống")

    refund = stripe.Refund.create(payment_intent=order.payment_intent_id)
    order.payment_status = PaymentStatus.REFUNDED
    db.commit()
    return {"refund_id": refund.id, "status": refund.status}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Nguồn tin cậy duy nhất để cập nhật trạng thái đơn hàng.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(400, detail=f"Webhook Error: {str(e)}")

    data_obj = event["data"]["object"]
    order_id = data_obj.get("metadata", {}).get("order_id")

    if order_id:
        order = db.query(Order).filter(Order.id == int(order_id)).first()
        if order:
            # Tự động map các sự kiện quan trọng
            if event["type"] == "payment_intent.succeeded":
                order.payment_status = PaymentStatus.PAID
                db.commit()
            elif event["type"] in ["payment_intent.payment_failed", "payment_intent.canceled"]:
                # Có thể giữ PENDING hoặc chuyển sang FAILED tùy logic của bạn
                order.payment_status = PaymentStatus.PENDING
                db.commit()
            elif event["type"] == "charge.refunded":
                order.payment_status = PaymentStatus.REFUNDED
                db.commit()

    return {"received": True}
