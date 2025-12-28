from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, ForeignKey
from app.db.base_class import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(15,2), nullable=False)
    original_price = Column(DECIMAL(15,2))
    discount_percent = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="SET NULL"))
    rating_avg = Column(DECIMAL(2,1), default=0)
    reviews_count = Column(Integer, default=0)
    sold_count = Column(Integer, default=0)
    main_image = Column(Text)
    is_new = Column(Boolean, default=False)
