from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse
from app.api.deps import get_current_active_admin

router = APIRouter(prefix="/products", tags=["Products"])

# GET /products: Lấy danh sách (Public)
@router.get("/", response_model=List[ProductResponse])
def read_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    size: int = Query(10, ge=1, le=100, description="Số lượng mỗi trang"),
    min_price: Optional[Decimal] = Query(None, description="Giá tối thiểu"),
    max_price: Optional[Decimal] = Query(None, description="Giá tối đa"),
    category_id: Optional[int] = Query(None, description="Lọc theo ID danh mục"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên")
):
    skip = (page - 1) * size
    query = db.query(Product)

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.offset(skip).limit(size).all()
    return products

# GET /products/{id}: Chi tiết sản phẩm (Public)
@router.get("/{id}", response_model=ProductResponse)
def read_product_detail(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    return product

# POST /products: Thêm sản phẩm (Admin)
@router.post("/", response_model=ProductResponse)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin) # Yêu cầu Token & Admin
):
    product = Product(**product_in.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product