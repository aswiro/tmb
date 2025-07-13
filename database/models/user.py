# database/models/user.py
import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

from database import Base


class UserStatus(enum.Enum):
    ACTIVE = "active"
    LEFT = "left"
    BANNED = "banned"


class MemberStatus(enum.Enum):
    MEMBER = "member"
    ADMIN = "admin"
    CREATOR = "creator"
    LEFT = "left"
    BANNED = "banned"


class User(Base):
    __tablename__ = "users"

    # Составные индексы для оптимизации частых запросов
    __table_args__ = (
        Index("idx_user_status_created", "status", "created_at"),
        Index("idx_user_invited_by_status", "invited_by", "status"),
        Index("idx_user_points_status", "points", "status"),
        Index("idx_user_last_active", "last_active_at"),
        Index(
            "idx_user_username_lower", text("LOWER(username)")
        ),  # Для поиска без учета регистра
    )

    # Primary key
    id = Column(BigInteger, primary_key=True)  # Telegram user ID

    # Telegram user data (размеры согласно ограничениям Telegram API)
    username = Column(String(32), nullable=True, index=True)  # Telegram max 32
    first_name = Column(String(64), nullable=True)  # Telegram max 64
    last_name = Column(String(64), nullable=True)  # Telegram max 64
    language_code = Column(String(5), default="en")  # ISO + region code
    is_bot = Column(Boolean, default=False, index=True)
    is_premium = Column(Boolean, default=False)  # Telegram Premium status

    # Bot interaction fields
    points = Column(Integer, default=0, index=True)
    invited_by = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    invitation_count = Column(Integer, default=0)
    total_bonuses_earned = Column(Integer, default=0)

    # Status tracking с использованием enum
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_active_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Оптимизированные relationships
    invited_users = relationship(
        "User",
        backref=backref("inviter", lazy="select"),
        remote_side=[id],
        lazy="select",  # Изменено с "dynamic" на "select", так как "dynamic" нельзя использовать с many-to-one
        foreign_keys=[invited_by],
    )

    group_memberships = relationship(
        "GroupMember",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    captcha_sessions = relationship(
        "CaptchaSession", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

    @property
    def full_name(self):
        """Полное имя пользователя"""
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts)) or f"User_{self.id}"

    @property
    def is_active(self):
        """Проверка активности пользователя"""
        return self.status == UserStatus.ACTIVE and not self.is_deleted


class GroupMember(Base):
    __tablename__ = "group_members"

    # Составные индексы и ограничения
    __table_args__ = (
        # Уникальность пользователя в группе
        UniqueConstraint("user_id", "group_id", name="uq_user_group"),
        # Индексы для частых запросов
        Index("idx_group_member_user_group", "user_id", "group_id"),
        Index("idx_group_member_status_joined", "status", "joined_at"),
        Index("idx_group_member_group_status", "group_id", "status"),
        Index("idx_group_member_warnings", "warnings_count", "last_warning_at"),
        Index("idx_group_member_muted", "muted_until"),
    )

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign keys
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False, index=True)

    # Status с использованием enum
    status = Column(Enum(MemberStatus), default=MemberStatus.MEMBER, index=True)

    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    left_at = Column(DateTime(timezone=True), nullable=True)

    # Moderation fields
    warnings_count = Column(Integer, default=0, index=True)
    last_warning_at = Column(DateTime(timezone=True), nullable=True, index=True)
    muted_until = Column(DateTime(timezone=True), nullable=True, index=True)

    # Дополнительные поля для модерации
    banned_until = Column(DateTime(timezone=True), nullable=True)
    ban_reason = Column(String(500), nullable=True)

    # Статистика активности
    messages_count = Column(Integer, default=0)
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="group_memberships")
    group = relationship("Group", back_populates="members")

    def __repr__(self):
        return f"<GroupMember(user_id={self.user_id}, group_id={self.group_id}, status={self.status})>"

    @property
    def is_active_member(self):
        """Проверка активного членства"""
        return self.status in [
            MemberStatus.MEMBER,
            MemberStatus.ADMIN,
            MemberStatus.CREATOR,
        ]

    @property
    def is_muted(self):
        """Проверка заглушки"""
        if not self.muted_until:
            return False
        return func.now() < self.muted_until

    @property
    def is_banned(self):
        """Проверка бана"""
        if not self.banned_until:
            return self.status == MemberStatus.BANNED
        return func.now() < self.banned_until

    def can_send_messages(self):
        """Может ли пользователь отправлять сообщения"""
        return self.is_active_member and not self.is_muted and not self.is_banned


# Дополнительная модель для отслеживания активности
class UserActivity(Base):
    __tablename__ = "user_activity"

    __table_args__ = (
        Index("idx_user_activity_user_date", "user_id", "activity_date"),
        Index("idx_user_activity_date", "activity_date"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    activity_date = Column(DateTime(timezone=True), nullable=False)
    messages_sent = Column(Integer, default=0)
    commands_used = Column(Integer, default=0)
    
    # Relationship
    user = relationship("User")