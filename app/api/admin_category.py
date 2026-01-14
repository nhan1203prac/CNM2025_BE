from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product 
from app.schemas.admin_category import CategoryCreate, CategoryUpdate
from app.api.deps import get_current_active_admin
from typing import List

router = APIRouter()

@router.get("/")
def get_categories(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin),
    search: str = Query(None),
    status: str = Query(None)
):
    query = db.query(Category)

    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    
    if status == "Hiển thị":
        query = query.filter(Category.is_active == True)
    elif status == "Đang ẩn":
        query = query.filter(Category.is_active == False)

    categories = query.all()

    results = []
    for cat in categories:
        p_count = db.query(func.count(Product.id)).filter(Product.category_id == cat.id).scalar()
        
        results.append({
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "imageUrl": cat.image_url, 
            "status": cat.is_active,
            "productCount": p_count or 0
        })

    return results

@router.post("/")
def create_category(
    category_in: CategoryCreate, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    if db.query(Category).filter(Category.slug == category_in.slug).first():
        raise HTTPException(status_code=400, detail="Slug đã tồn tại")
    
    new_cat = Category(**category_in.model_dump())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return {"message": "Tạo thành công", "id": new_cat.id}

@router.patch("/{cat_id}")
def update_category(
    cat_id: int, 
    category_in: CategoryUpdate, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    db_cat = db.query(Category).filter(Category.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")
    
    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cat, key, value)
    
    db.commit()
    return {"message": "Cập nhật thành công"}

@router.delete("/{cat_id}")
def delete_category(
    cat_id: int, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    db_cat = db.query(Category).filter(Category.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Không tìm thấy")
    
    # has_products = db.query(Product).filter(Product.category_id == cat_id).first()
    # if has_products:
    #     raise HTTPException(status_code=400, detail="Danh mục này đang có sản phẩm, không thể xóa!")

    db_cat.is_active = False

    # db.delete(db_cat)
    db.commit()
    return {"message": "Đã ẩn danh mục"}