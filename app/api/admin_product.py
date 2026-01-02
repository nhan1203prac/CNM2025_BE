from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.product import Product
from app.models.category import Category
from app.models.product_image import ProductImage 
from app.schemas.admin_product import ProductCreate, ProductUpdate
from app.api.deps import get_current_active_admin
from typing import Optional
router = APIRouter()

@router.get("")
def get_products(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin),
    search: Optional[str] = Query(None),       
    category_id: Optional[int] = Query(None)
):
    query = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.images) 
    )

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.id.desc()).all()

    results = []
    for p in products:
        results.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "category": p.category.name if p.category else "N/A",
            "imageUrl": p.main_image,
            "is_new": p.is_new,
            "category_id": p.category_id,
            "status": "Còn hàng" if p.stock > 0 else "Hết hàng",
            "sub_images": [img.image_url for img in p.images] if hasattr(p, 'images') else []
        })
    return results

@router.post("")
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    product_data = product_in.model_dump(exclude={'images'})
    new_prod = Product(**product_data)
    db.add(new_prod)
    db.flush()

    if product_in.images:
        for url in product_in.images:
            db.add(ProductImage(product_id=new_prod.id, image_url=url))
    
    db.commit()
    return {"message": "Tạo thành công", "id": new_prod.id}


@router.patch("/{prod_id}")
def update_product(
    prod_id: int, 
    product_in: ProductUpdate, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    db_prod = db.query(Product).filter(Product.id == prod_id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    update_data = product_in.model_dump(exclude={'images'}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prod, key, value)
    
    if product_in.images is not None:
        db.query(ProductImage).filter(ProductImage.product_id == prod_id).delete()
        
        for url in product_in.images:
            db.add(ProductImage(product_id=prod_id, image_url=url))
    
    db.commit()
    db.refresh(db_prod)
    return {"message": "Cập nhật sản phẩm thành công"}


@router.delete("/{prod_id}")
def delete_product(prod_id: int, db: Session = Depends(get_db)):
    db_prod = db.query(Product).filter(Product.id == prod_id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    db.delete(db_prod)
    db.commit()
    return {"message": "Xóa thành công"}