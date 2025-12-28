from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey, text
from app.db.base_class import Base

class Profile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)
    dob = Column(Date, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
