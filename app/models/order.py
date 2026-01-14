from sqlalchemy import Column, String, Integer, DECIMAL, TIMESTAMP, ForeignKey,text,Enum, Numeric
from app.db.base_class import Base
from sqlalchemy.orm import relationship
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"

class ShippingStatus(str, enum.Enum):
    PENDING = "PENDING"
    SHIPPING = "SHIPPING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(DECIMAL(15,2), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    shipping_status = Column(Enum(ShippingStatus), default=ShippingStatus.PENDING, nullable=False)
    shipping_fee = Column(Numeric(10, 2), default=0)
    subtotal = Column(Numeric(10, 2))
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)
    expected_delivery_date = Column(String, nullable=True) 
    delivery_deadline = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    user = relationship("User", backref="orders")
    address_detail = relationship("Address")

