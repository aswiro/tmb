from sqlalchemy import BigInteger, Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(BigInteger, primary_key=True)  # Telegram group ID
    title = Column(String(100), nullable=False)
    username = Column(String(30), nullable=True, index=True)

    # Bot status in group
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    members = relationship("GroupMember", back_populates="group")
    filter_rules = relationship("FilterRule", back_populates="group")
    captcha_settings = relationship("CaptchaSetting", back_populates="group")