from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey
from app.db.base_class import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(DECIMAL(15,2), nullable=False)
    selected_size = Column(String(20))
    selected_color = Column(String(50))
