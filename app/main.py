from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.db.base import Base 
from app.db.session import engine

app = FastAPI(title="FastAPI E-commerce API")
#Tạo bảng trong sql
Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "OK"}
