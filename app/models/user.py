from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text
from app.db.base_class import Base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    isAdmin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )
    verification_code = Column(String(100), nullable=True)
    password_reset_token = Column(String(100), nullable=True)

    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True)
    profile = relationship("Profile", back_populates="user")
