from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import desc
from app.db.session import get_db
from app.models.product import Product
from app.models.favorite import Favorite
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, PaginatedProductResponse, ProductDetailResponse
from app.api.deps import get_current_active_admin
from app.api.deps import get_optional_current_user
router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=PaginatedProductResponse) 
def read_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=100), 
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    category_id: Optional[int] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    search: Optional[str] = Query(None),
    current_user = Depends(get_optional_current_user)
):
    # 1. Khởi tạo Query
    query = db.query(Product)

    # 2. Áp dụng Filters
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if rating:
        query = query.filter(Product.rating_avg >= rating)

    # 3. Pagination & Sorting
    query = query.order_by(desc(Product.id))
    total_items = query.count()
    total_pages = (total_items + size - 1) // size
    skip = (page - 1) * size
    products = query.offset(skip).limit(size).all()


    fav_set = set()

    if current_user:
        fav_ids = db.query(Favorite.product_id).filter(Favorite.user_id == current_user.id).all()
        fav_set = {f[0] for f in fav_ids}

    final_products = []
    
    for p in products:
        product_data = ProductResponse.model_validate(p) 
        
        product_data.is_favorite = (p.id in fav_set)

        final_products.append(product_data)
    return {
        "items": final_products, 
        "total": total_items,
        "page": page,
        "size": size,
        "pages": total_pages
    }

# app/api/v1/endpoints/products.py

@router.get("/{id}", response_model=ProductDetailResponse)
def read_product_detail(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    related_products = db.query(Product).filter(
        Product.category_id == product.category_id,
        Product.id != id
    ).limit(4).all()

    colors = [
        v.variant_value for v in product.variants 
        if v.variant_type and v.variant_type.strip().lower() == "color"
    ]
    storages = [
        v.variant_value for v in product.variants 
        if v.variant_type and v.variant_type.strip().lower() == "storage"
    ]
    sizes = [
        v.variant_value for v in product.variants 
        if v.variant_type and v.variant_type.strip().lower() == "size"
    ]

    return {
        "product": product,
        "related": related_products,
        "colors": colors,
        "storages": storages,
        "sizes": sizes
    }

# # POST /products: Thêm sản phẩm (Admin)
# @router.post("/", response_model=ProductResponse)
# def create_product(
#     product_in: ProductCreate,
#     db: Session = Depends(get_db),
#     current_admin = Depends(get_current_active_admin) # Yêu cầu Token & Admin
# ):
#     product = Product(**product_in.dict())
#     db.add(product)
#     db.commit()
#     db.refresh(product)
#     return product