from fastapi import FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware
from app.api.auth import router as auth_router
from app.api.product import router as product_router
from app.api.category import router as category_router
from app.api.cart import router as cart_router
from app.api.favorites import router as favorites_router
from app.db.base import Base
from app.db.session import engine
from app.core.config import settings

security = HTTPBearer()

app = FastAPI(
    title="FastAPI E-commerce API",
    swagger_ui_parameters={"syntaxHighlight.theme": "monokai"},
)

# Add SessionMiddleware for Google OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1") # /api/v1/products
app.include_router(category_router, prefix="/api/v1") # /api/v1/categories
app.include_router(cart_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "OK"}

# Custom OpenAPI schema để thêm Bearer token authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="FastAPI E-commerce API",
        version="1.0.0",
        description="E-commerce API with authentication",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Nhập JWT token (không cần 'Bearer ' prefix, nó sẽ tự động thêm)"
        }
    }
    
    # Áp dụng security cho tất cả endpoints (ngoại trừ register, login, etc)
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
