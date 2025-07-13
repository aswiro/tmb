from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class CaptchaSetting(Base):
    __tablename__ = "captcha_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False)

    # CAPTCHA configuration
    captcha_type = Column(String(20), default="standard")  # standard, math
    captcha_size = Column(
        Integer, default=2
    )  # 0-12 (1=320x180, 2=640x360, 3=960x540, 4=1280x720)
    difficulty_level = Column(Integer, default=3)  # 0-6
    multicolor = Column(Boolean, default=False)
    chars_mode = Column(String(7), default="nums")  # nums, hex, ascii
    margin = Column(Boolean, default=False)
    allow_multiplication = Column(Boolean, default=False)

    # Timing settings
    timeout_seconds = Column(Integer, default=300)  # 5 minutes
    auto_kick_on_fail = Column(Boolean, default=True)
    max_attempts = Column(Integer, default=3)

    # Advanced settings
    trusted_users = Column(JSON, nullable=True)  # User IDs that skip CAPTCHA

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    group = relationship("Group", back_populates="captcha_settings")
    sessions = relationship("CaptchaSession", back_populates="captcha_setting")


class CaptchaSession(Base):
    __tablename__ = "captcha_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False)
    captcha_setting_id = Column(
        BigInteger, ForeignKey("captcha_settings.id"), nullable=False
    )

    # Session data
    question = Column(Text, nullable=False)
    correct_answer = Column(String(255), nullable=False)
    attempts_made = Column(Integer, default=0)
    status = Column(
        String(20), default="pending"
    )  # pending, completed, failed, expired

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Message tracking
    message_id = Column(BigInteger, nullable=True)  # CAPTCHA message ID for deletion

    # Relationships
    user = relationship("User", back_populates="captcha_sessions")
    captcha_setting = relationship("CaptchaSetting", back_populates="sessions")
