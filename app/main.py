from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.product import router as product_router
from app.api.category import router as category_router
from app.db.base import Base 
from app.api.cart import router as cart_router
from app.api.favorites import router as favorites_router
from app.db.base import Base
from app.api.cart import router as cart_router
from app.api.favorites import router as favorites_router
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="FastAPI E-commerce API")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1") # /api/v1/products
app.include_router(category_router, prefix="/api/v1") # /api/v1/categories
app.include_router(cart_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "OK"}
