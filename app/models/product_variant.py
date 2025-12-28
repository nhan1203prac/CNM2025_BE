from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base_class import Base

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_type = Column(String(20))
    variant_value = Column(String(50))
