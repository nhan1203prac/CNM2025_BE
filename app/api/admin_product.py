from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.product import Product
from app.models.category import Category
from app.models.product_image import ProductImage 
from app.schemas.admin_product import ProductCreate, ProductUpdate
from app.api.deps import get_current_active_admin
from typing import Optional, List
from sqlalchemy import desc

router = APIRouter()

@router.get("")
def get_products(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin),
    search: Optional[str] = Query(None),       
    category_id: Optional[int] = Query(None)
):
    # Load thêm variants để tránh lỗi "lazy loading"
    query = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.images),
        joinedload(Product.variants) # Load thêm cái này
    )

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.id.desc()).all()

    results = []
    for p in products:
        # Bóc tách variants thành các mảng riêng biệt
        colors = [v.variant_value for v in p.variants if v.variant_type.lower() == "color"]
        storages = [v.variant_value for v in p.variants if v.variant_type.lower() == "storage"]
        sizes = [v.variant_value for v in p.variants if v.variant_type.lower() == "size"]

        results.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "category": p.category.name if p.category else "N/A",
            "imageUrl": p.main_image,
            "category_id": p.category_id,
            "sub_images": [img.image_url for img in p.images],
            "colors": colors,
            "storages": storages,
            "sizes": sizes,
            "description": p.description
        })
    return results

from app.models.product_variant import ProductVariant 

@router.post("")
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    data = product_in.model_dump(exclude={'images', 'colors', 'storages', 'sizes'})
    new_prod = Product(**data)
    db.add(new_prod)
    db.flush() 

    if product_in.images:
        for url in product_in.images:
            db.add(ProductImage(product_id=new_prod.id, image_url=url))
    
    for c in (product_in.colors or []):
        db.add(ProductVariant(product_id=new_prod.id, variant_type="color", variant_value=c))
    for s in (product_in.storages or []):
        db.add(ProductVariant(product_id=new_prod.id, variant_type="storage", variant_value=s))
    for sz in (product_in.sizes or []):
        db.add(ProductVariant(product_id=new_prod.id, variant_type="size", variant_value=sz))

    db.commit()
    return {"message": "Tạo thành công", "id": new_prod.id}

@router.patch("/{prod_id}")
def update_product(prod_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    db_prod = db.query(Product).filter(Product.id == prod_id).first()
    if not db_prod: raise HTTPException(404, "Không tìm thấy")
    
    update_data = product_in.model_dump(exclude={'images', 'colors', 'storages', 'sizes'}, exclude_unset=True)
    for k, v in update_data.items(): setattr(db_prod, k, v)
    
    if product_in.images is not None:
        db.query(ProductImage).filter(ProductImage.product_id == prod_id).delete()
        for url in product_in.images: db.add(ProductImage(product_id=prod_id, image_url=url))

    if any(x is not None for x in [product_in.colors, product_in.storages, product_in.sizes]):
        db.query(ProductVariant).filter(ProductVariant.product_id == prod_id).delete()
        for c in (product_in.colors or []):
            db.add(ProductVariant(product_id=prod_id, variant_type="color", variant_value=c))
        for s in (product_in.storages or []):
            db.add(ProductVariant(product_id=prod_id, variant_type="storage", variant_value=s))
        for sz in (product_in.sizes or []):
            db.add(ProductVariant(product_id=prod_id, variant_type="size", variant_value=sz))

    db.commit()
    return {"message": "Cập nhật thành công"}


@router.delete("/{prod_id}")
def delete_product(
    prod_id: int, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    db_prod = db.query(Product).filter(Product.id == prod_id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    db.delete(db_prod)
    db.commit()
    return {"message": "Xóa thành công"}