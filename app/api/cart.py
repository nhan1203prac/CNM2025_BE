from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.cart_item import CartItem
from app.models.product import Product

router = APIRouter(prefix="/cart", tags=["Cart"])

#  HARD CODE USER ĐỂ TEST
USER_ID = 1

# code lấy userid
# @router.get("")
# def get_cart(
#     db: Session = Depends(get_db),
#     user = Depends(get_current_user)
# ):
 # return db.query(CartItem).filter(CartItem.user_id == user.id).all()
@router.get("")
def get_cart(
    db: Session = Depends(get_db),
):
    return db.query(CartItem).filter(CartItem.user_id == USER_ID).all()


@router.post("/add")
def add_to_cart(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product không tồn tại")

    item = db.query(CartItem).filter(
        CartItem.user_id == USER_ID,
        CartItem.product_id == product_id
    ).first()

    if item:
        item.quantity += 1
    else:
        db.add(CartItem(user_id=USER_ID, product_id=product_id, quantity=1))

    db.commit()
    return {"message": "Added to cart"}


@router.delete("/{id}")
def delete_or_decrease(
    id: int,
    db: Session = Depends(get_db),
):
    item = db.query(CartItem).filter(
        CartItem.id == id,
        CartItem.user_id == USER_ID
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Cart item không tồn tại")

    if item.quantity > 1:
        item.quantity -= 1
    else:
        db.delete(item)

    db.commit()
    return {"message": "Updated cart"}
