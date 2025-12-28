from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from app.db.base_class import Base

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_name = Column(String(255))
    receiver_phone = Column(String(20))
    province = Column(String(100))
    district = Column(String(100))
    ward = Column(String(100))
    street_details = Column(Text)
    type = Column(String(20))
    is_default = Column(Boolean, default=False)
