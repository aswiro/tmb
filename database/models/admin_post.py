import enum
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class PostStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    ERROR = "error"


class MediaType(enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    ANIMATION = "animation"


class PollType(enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    QUIZ = "quiz"


class AdminPost(Base):
    __tablename__ = "admin_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    media_type = Column(Enum(MediaType), nullable=True)
    media_file_id = Column(String(255), nullable=True)  # Telegram file_id
    media_caption = Column(Text, nullable=True)
    hashtags = Column(ARRAY(String), nullable=True)  # Массив хештегов
    links = Column(JSON, nullable=True)  # Массив ссылок с описанием
    target_groups = Column(ARRAY(Integer), nullable=True)  # ID групп для публикации
    categories = Column(ARRAY(String(100)), nullable=True)  # Категории поста
    scheduled_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Время запланированной публикации
    published_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Время фактической публикации
    expires_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Время окончания показа
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Приоритет показа
    is_template = Column(Boolean, default=False, nullable=False)  # Является ли пост шаблоном
    template_name = Column(String(255), nullable=True)  # Название шаблона
    template_description = Column(Text, nullable=True)  # Описание шаблона
    error_message = Column(Text, nullable=True)  # Текст ошибки при отправке
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    analytics = relationship(
        "PostAnalytics", back_populates="post", cascade="all, delete-orphan"
    )
    published_posts = relationship(
        "PublishedPost", back_populates="post", cascade="all, delete-orphan"
    )
    poll = relationship(
        "Poll", back_populates="post", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AdminPost(id={self.id}, title='{self.title}', status={self.status})>"

    @property
    def is_published(self):
        """Проверка, опубликован ли пост"""
        return self.status == PostStatus.PUBLISHED

    @property
    def is_scheduled(self):
        """Проверка, запланирован ли пост"""
        return self.status == PostStatus.SCHEDULED

    @property
    def is_expired(self):
        """Проверка, истек ли срок поста"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    @property
    def has_error(self):
        """Проверка, есть ли ошибка при отправке"""
        return self.status == PostStatus.ERROR


class PostAnalytics(Base):
    __tablename__ = "post_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(
        Integer, ForeignKey("admin_posts.id", ondelete="CASCADE"), nullable=False
    )
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False)
    views_count = Column(Integer, default=0, nullable=False)
    clicks_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    reactions = Column(JSON, nullable=True)  # {'like': 10, 'dislike': 2, 'heart': 5}
    view_duration = Column(Integer, nullable=True)  # Среднее время просмотра в секундах
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    post = relationship("AdminPost", back_populates="analytics")
    group = relationship("Group")

    def __repr__(self):
        return f"<PostAnalytics(id={self.id}, post_id={self.post_id}, group_id={self.group_id})>"

    @property
    def total_interactions(self):
        """Общее количество взаимодействий"""
        return self.views_count + self.clicks_count + self.shares_count

    @property
    def click_through_rate(self):
        """Коэффициент кликабельности (CTR)"""
        if self.views_count == 0:
            return 0.0
        return (self.clicks_count / self.views_count) * 100

    @property
    def engagement_rate(self):
        """Коэффициент вовлеченности"""
        if self.views_count == 0:
            return 0.0
        total_reactions = sum(self.reactions.values()) if self.reactions else 0
        return (
            (self.clicks_count + self.shares_count + total_reactions) / self.views_count
        ) * 100


class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(
        Integer, ForeignKey("admin_posts.id", ondelete="CASCADE"), nullable=False
    )
    question = Column(Text, nullable=False)
    poll_type = Column(Enum(PollType), default=PollType.SINGLE_CHOICE, nullable=False)
    is_anonymous = Column(Boolean, default=True, nullable=False)
    allows_multiple_answers = Column(Boolean, default=False, nullable=False)
    correct_option_id = Column(Integer, nullable=True)  # Для викторин
    explanation = Column(Text, nullable=True)  # Объяснение правильного ответа
    open_period = Column(Integer, nullable=True)  # Время в секундах
    close_date = Column(DateTime(timezone=True), nullable=True)
    is_closed = Column(Boolean, default=False, nullable=False)
    total_voter_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)  # Текст ошибки при отправке
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    post = relationship("AdminPost", back_populates="poll")
    options = relationship(
        "PollOption", back_populates="poll", cascade="all, delete-orphan"
    )
    votes = relationship(
        "PollVote", back_populates="poll", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Poll(id={self.id}, question='{self.question[:50]}...')>"

    @property
    def is_quiz(self):
        """Проверка, является ли опрос викториной"""
        return self.correct_option_id is not None


class PollOption(Base):
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(
        Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )
    text = Column(String(100), nullable=False)
    voter_count = Column(Integer, default=0, nullable=False)
    position = Column(Integer, nullable=False)  # Порядок опции

    # Relationships
    poll = relationship("Poll", back_populates="options")
    votes = relationship(
        "PollVote", back_populates="option", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<PollOption(id={self.id}, text='{self.text}', votes={self.voter_count})>"
        )

    @property
    def percentage(self):
        """Процент голосов за эту опцию"""
        if self.poll.total_voter_count == 0:
            return 0.0
        return (self.voter_count / self.poll.total_voter_count) * 100


class PollVote(Base):
    __tablename__ = "poll_votes"
    __table_args__ = (
        UniqueConstraint("poll_id", "user_id", name="unique_poll_user_vote"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(
        Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )
    option_id = Column(
        Integer, ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    voted_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    poll = relationship("Poll", back_populates="votes")
    option = relationship("PollOption", back_populates="votes")
    user = relationship("User")

    def __repr__(self):
        return (
            f"<PollVote(id={self.id}, poll_id={self.poll_id}, user_id={self.user_id})>"
        )


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(
        Integer, ForeignKey("admin_posts.id", ondelete="CASCADE"), nullable=False
    )
    chat_id = Column(BigInteger, nullable=False)  # ID чата/канала
    message_id = Column(Integer, nullable=False)  # ID сообщения в Telegram
    published_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_edited = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    post = relationship("AdminPost", back_populates="published_posts")

    def __repr__(self):
        return f"<PublishedPost(id={self.id}, post_id={self.post_id}, chat_id={self.chat_id}, message_id={self.message_id})>"
