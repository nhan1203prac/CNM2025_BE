from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.cart_item import CartItem
from app.models.product import Product
from app.api.deps import get_current_user 
from typing import List

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("")
def get_cart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cart_items = db.query(CartItem)\
        .options(joinedload(CartItem.product))\
        .filter(CartItem.user_id == current_user.id)\
        .all()
    
    return [
        {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "name": item.product.name,
            "price": item.product.price,
            "image": item.product.main_image,
            "stock": item.product.stock
        } for item in cart_items
    ]

@router.post("/add")
def add_to_cart(
    product_id: int,
    quantity: int = 1, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) 
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()

    if item:
        item.quantity += quantity 
    else:
        db.add(CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity))

    db.commit()
    return {"message": "Đã thêm vào giỏ hàng"}

@router.delete("/{id}")
def delete_or_decrease(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    item = db.query(CartItem).filter(
        CartItem.id == id,
        CartItem.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Sản phẩm trong giỏ không tồn tại")

    if item.quantity > 1:
        item.quantity -= 1
    else:
        db.delete(item)

    db.commit()
    return {"message": "Cập nhật giỏ hàng thành công"}