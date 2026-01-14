from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func 
from typing import List
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product 

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/all")
def get_all_categories(db: Session = Depends(get_db)):
    results = db.query(
        Category, 
        func.count(Product.id).label("total")
    ).outerjoin(Product, Category.id == Product.category_id)\
     .filter(Category.is_active == True)\
     .group_by(Category.id)\
     .all()

    return [
        {
            "id": cat.id,
            "name": cat.name,
            "img": cat.image_url,
            "product_count": f"{total}+"
        } for cat, total in results
    ]