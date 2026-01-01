from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.favorite import Favorite
from app.models.product import Product
from app.api.deps import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.get("/")
def get_favorites(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) 
):
    favorites = db.query(Product).join(
        Favorite, Favorite.product_id == Product.id
    ).filter(Favorite.user_id == current_user.id).all()
    
    return favorites


@router.post("/{product_id}")
def toggle_favorite(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.product_id == product_id
    ).first()

    if fav:
        db.delete(fav)
        db.commit()
        return {"status": "removed", "is_favorite": False}

    db.add(Favorite(user_id=current_user.id, product_id=product_id))
    db.commit()
    return {"status": "added", "is_favorite": True}