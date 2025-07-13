from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Boolean

from database import Base


class FilterRule(Base):
    __tablename__ = "filter_rules"

    id = Column(
        BigInteger,
        ForeignKey("groups.id"),
        primary_key=True,
        nullable=False,
        unique=True,
    )
    hashtag = Column(Boolean, nullable=False, default=False)
    url = Column(Boolean, nullable=False, default=False)
    email = Column(Boolean, nullable=False, default=False)
    ads = Column(Boolean, nullable=False, default=False)
    phone_number = Column(Boolean, nullable=False, default=False)
    forbidden_words = Column(Boolean, nullable=False, default=False)
    track_members = Column(Boolean, nullable=False, default=False)
    max_message_length = Column(Integer, nullable=False, default=50)
    bonuses_enabled = Column(Boolean, nullable=False, default=False)
    bonus_per_user = Column(Integer, nullable=False, default=10)
    bonus_checkpoint = Column(Integer, nullable=False, default=1000)
    captcha = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    group = relationship("Group", back_populates="filter_rules")
