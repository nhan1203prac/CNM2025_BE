from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.product import Product
from app.models.category import Category
from app.models.favorite import Favorite
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/home", tags=["Home"])

@router.get("/")
def get_home_page_data(db: Session = Depends(get_db), current_user = Depends(get_optional_current_user)):
    categories_query = db.query(
        Category, 
        func.count(Product.id).label("total")
    ).outerjoin(Product, Category.id == Product.category_id).group_by(Category.id).limit(8).all()

    categories_data = [
        {
            "id": cat.id,
            "name": cat.name,
            "img": cat.image_url,
            "product_count": f"{total/1000:.1f}k+" if total >= 1000 else f"{total}+"
        } for cat, total in categories_query
    ]

    products = db.query(Product).order_by(Product.sold_count.desc()).limit(20).all() 
    
    fav_ids = set() 
    if current_user:
        fav_ids = {f.product_id for f in db.query(Favorite.product_id).filter(Favorite.user_id == current_user.id).all()}

    best_sellers_data = []
    for p in products:
        product_dict = {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "original_price": p.original_price,
            "discount_percent": p.discount_percent,
            "main_image": p.main_image,
            "rating_avg": p.rating_avg,
            "reviews_count": p.reviews_count,
            "sold_count": p.sold_count,
            "category_id": p.category_id,
            "is_new": p.is_new,
            "is_favorite": p.id in fav_ids 
        }
        best_sellers_data.append(product_dict)

    return {
        "featured_categories": categories_data,
        "best_sellers": best_sellers_data
    }