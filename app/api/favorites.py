from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.favorite import Favorite
from app.models.product import Product

router = APIRouter(prefix="/favorites", tags=["Favorites"])

#  HARD CODE USER ĐỂ TEST
USER_ID = 1

# code lấy userid
# @router.get("")
# def get_favorites(
#     db: Session = Depends(get_db),
#     user = Depends(get_current_user)
# ):
#     return db.query(Favorite).filter(
#         Favorite.user_id == user.id
#     ).all()
@router.get("")
def get_favorites(
    db: Session = Depends(get_db),
):
    return db.query(Favorite).filter(Favorite.user_id == USER_ID).all()


@router.post("/{product_id}")
def toggle_favorite(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product không tồn tại")

    fav = db.query(Favorite).filter(
        Favorite.user_id == USER_ID,
        Favorite.product_id == product_id
    ).first()

    if fav:
        db.delete(fav)
        db.commit()
        return {"message": "Removed from favorites"}

    db.add(Favorite(user_id=USER_ID, product_id=product_id))
    db.commit()
    return {"message": "Added to favorites"}
