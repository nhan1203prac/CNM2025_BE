from sqlalchemy import Column, String, Integer, DECIMAL, TIMESTAMP, ForeignKey,text
from app.db.base_class import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(DECIMAL(15,2), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
