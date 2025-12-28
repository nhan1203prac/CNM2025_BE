from sqlalchemy import Column, Integer, String, Text
from app.db.base_class import Base

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    logo_url = Column(Text)
