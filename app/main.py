from fastapi import FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware
from app.api.auth import router as auth_router
from app.api.product import router as product_router
from app.api.category import router as category_router
from app.api.cart import router as cart_router
from app.api.favorites import router as favorites_router
from app.api.orders import router as orders_router
from app.api.home_data import router as home_data_router
from app.api.admin import router as admin_router
from app.api.admin_order import router as admin_order_router
from app.api.admin_category import router as admin_category_router
from app.api.admin_product import router as admin_product_router
from app.api.admin_user import router as admin_user_router
from app.api.profile import router as profile_dashboard
from app.api.address import router as address
from app.api.notification import router as notifications
from app.api.payment import router as payment_router

from app.db.base import Base
from app.db.session import engine
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

security = HTTPBearer()

app = FastAPI(
    title="FastAPI E-commerce API",
    swagger_ui_parameters={"syntaxHighlight.theme": "monokai"},
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine) 

app.include_router(auth_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1") 
app.include_router(category_router, prefix="/api/v1") 
app.include_router(cart_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")
app.include_router(home_data_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1/admin")
app.include_router(admin_order_router, prefix="/api/v1/admin")
app.include_router(admin_category_router, prefix="/api/v1/admin/categories")
app.include_router(admin_product_router, prefix="/api/v1/admin/products")
app.include_router(admin_user_router, prefix="/api/v1/admin/users")
app.include_router(profile_dashboard, prefix="/api/v1/profile-dashboard")
app.include_router(address, prefix="/api/v1/addresses")
app.include_router(notifications, prefix="/api/v1/notifications")

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
    
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
