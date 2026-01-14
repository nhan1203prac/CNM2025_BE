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

    # THÊM CÁC TRƯỜNG NÀY ĐỂ GỌI API GHN
    province_id = Column(Integer, nullable=True) # ID tỉnh của GHN
    district_id = Column(Integer, nullable=True) # ID huyện của GHN
    ward_code = Column(String(20), nullable=True) # Code phường của GHN
    street_details = Column(Text)
    type = Column(String(20))
    is_default = Column(Boolean, default=False)
