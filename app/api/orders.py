from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import uuid
from app.db.session import get_db
from app.models.order import Order, ShippingStatus 
from app.models.order_item import OrderItem
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.address import Address
from app.core.shipping import get_ghn_shipping_details
from app.schemas.order import OrderResponse, OrderCreateRequest
from app.api.deps import get_current_user
from typing import List

router = APIRouter(prefix="/orders", tags=["Orders"])

# POST /orders/checkout
@router.post("/create", status_code=201)
def createOrder(
    order_in: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) 
):
    address = db.query(Address).filter(
        Address.id == order_in.address_id, 
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Địa chỉ giao hàng không hợp lệ")
    
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Giỏ hàng trống")

    # GỌI 1 LẦN DUY NHẤT ĐỂ LẤY TẤT CẢ THÔNG TIN SHIP
    ship_details = get_ghn_shipping_details(
        to_district_id=address.district_id,
        to_ward_code=address.ward_code
    )

    new_order = Order(
        user_id=current_user.id,
        address_id=address.id,
        shipping_fee=ship_details["fee"],
        total_amount=0,
        subtotal=0,
        expected_delivery_date=ship_details["expected_delivery"],
        delivery_deadline=ship_details["deadline"],
        shipping_status="PENDING",
        payment_status="PENDING"
    )

    db.add(new_order)
    db.flush() 

    total_amount_products = 0
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product or product.stock < item.quantity:
            db.rollback() 
            raise HTTPException(status_code=400, detail=f"Sản phẩm {product.name if product else 'ID '+str(item.product_id)} không đủ hàng")

        product.stock -= item.quantity
        total_amount_products += product.price * item.quantity

        db.add(OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=item.quantity,
            price_at_purchase=product.price,
            selected_size=getattr(item, 'selected_size', None), 
            selected_color=getattr(item, 'selected_color', None) 
        ))
        db.delete(item)

    new_order.total_amount = total_amount_products
    new_order.subtotal = total_amount_products + ship_details["fee"]

    db.commit()
    db.refresh(new_order)

    return new_order



@router.get("/preview-shipping")
def preview_shipping(address_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Địa chỉ không hợp lệ")
    
    ship_details = get_ghn_shipping_details(
        to_district_id=address.district_id,
        to_ward_code=address.ward_code,
        weight=500
    )
    
    return {
        "fee": ship_details["fee"],
        "expected_delivery": ship_details["expected_delivery"],
        "deadline": ship_details["deadline"]
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

