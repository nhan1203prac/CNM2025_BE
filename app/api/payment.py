from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import stripe

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.order import Order, PaymentStatus
from app.models.notification import Notification

router = APIRouter(prefix="/payment", tags=["Payment"])


def _to_cents(amount: Decimal) -> int:
    """
    Biến 1500000.00 thành 1500000 (số nguyên)
    VND không dùng cent, nên không nhân 100.
    """
    return int(float(amount))

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
    print(f"DEBUG: My Key is: {settings.STRIPE_SECRET_KEY}")
    stripe.api_key = settings.STRIPE_SECRET_KEY

    order = _get_order(db, order_id, user.id)

    if order.payment_status == PaymentStatus.PAID:
        return {"status": "already_paid"}

    intent = stripe.PaymentIntent.create(
        amount=_to_cents(order.total_amount),
        currency=settings.STRIPE_CURRENCY,
        metadata={"order_id": order.id, "user_id": user.id},
        automatic_payment_methods={"enabled": True},
        idempotency_key=f"intent-order-{order.id}-{settings.STRIPE_CURRENCY.lower()}",
    )


    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "status": intent.status,
    }


@router.post("/confirm-order/{order_id}")
def confirm_order_manual(
    order_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    order.payment_status = PaymentStatus.PAID
    
    notification = Notification(
        user_id=order.user_id,
        title="Thanh toán thành công",
        content=f"Đơn hàng #{order.id} của bạn đã được thanh toán thành công!",
        type="payment"
    )
    db.add(notification)
    db.commit()

    return {"status": "success", "message": "Order updated to PAID"}

# @router.post("/refund/{order_id}")
# def refund_order(order_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
#     """Hoàn tiền đơn giản qua Payment Intent ID."""
#     order = _get_order(db, order_id, user.id)
#     if not order.payment_intent_id:
#         raise HTTPException(400, "Đơn hàng này chưa được thanh toán qua hệ thống")
#     if order.payment_status != PaymentStatus.PAID:
#         raise HTTPException(400, "Đơn hàng chưa thanh toán thành công, không thể hoàn tiền")

#     try:
#         intent = stripe.PaymentIntent.retrieve(order.payment_intent_id)
#         status_pi = intent.get("status")
#         if status_pi != "succeeded":
#             raise HTTPException(400, f"PaymentIntent chưa thành công (status={status_pi}), không thể hoàn tiền")

#         charges = intent.get("charges", {}).get("data", [])
#         if not charges:
#             raise HTTPException(400, "Không tìm thấy giao dịch (charge) để hoàn tiền")

#         charge_id = charges[0]["id"]
#         refund = stripe.Refund.create(charge=charge_id)

#         # Chỉ đánh dấu REFUNDED khi Stripe trả về thành công ngay
#         if getattr(refund, "status", None) == "succeeded":
#             order.payment_status = PaymentStatus.REFUNDED
#             db.commit()

#         return {"refund_id": refund.id, "status": refund.status}

#     except stripe.error.StripeError as e:  # type: ignore[attr-defined]
#         # Trả lỗi 400 có thông điệp rõ ràng thay vì 500
#         message = getattr(e, "user_message", None) or str(e)
#         raise HTTPException(400, detail=message)
#     except HTTPException:
#         # Ném lại các HTTPException đã được chuẩn hóa
#         raise
#     except Exception as e:
#         # Bắt mọi lỗi khác thành 400 để client hiểu được
#         raise HTTPException(400, detail=str(e))


# @router.post("/webhook")
# async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
#     """
#     Nguồn tin cậy duy nhất để cập nhật trạng thái đơn hàng.
#     """
#     payload = await request.body()
#     sig_header = request.headers.get("stripe-signature")

#     try:
#         event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
#     except Exception as e:
#         raise HTTPException(400, detail=f"Webhook Error: {str(e)}")

#     data_obj = event["data"]["object"]
#     order_id = data_obj.get("metadata", {}).get("order_id")

#     if order_id:
#         order = db.query(Order).filter(Order.id == int(order_id)).first()
#         if order:
#             # Tự động map các sự kiện quan trọng
#             if event["type"] == "payment_intent.succeeded":
#                 order.payment_status = PaymentStatus.PAID
                
#                 # Tạo thông báo cho user khi thanh toán thành công
#                 notification = Notification(
#                     user_id=order.user_id,
#                     title="Thanh toán thành công",
#                     content=f"Đơn hàng #{order.id} của bạn đã được thanh toán thành công. Tổng tiền: {order.total_amount} VND",
#                     type="payment"
#                 )
#                 db.add(notification)
#                 db.commit()
#             elif event["type"] in ["payment_intent.payment_failed", "payment_intent.canceled"]:
#                 # Có thể giữ PENDING hoặc chuyển sang FAILED tùy logic của bạn
#                 order.payment_status = PaymentStatus.PENDING
#                 db.commit()
#             elif event["type"] == "charge.refunded":
#                 order.payment_status = PaymentStatus.REFUNDED
#                 db.commit()

#     return {"received": True}
    
