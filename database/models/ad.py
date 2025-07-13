import enum

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class AdCampaignStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AdCreativeContentType(enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"


class AdCreativeStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AdEventType(enum.Enum):
    IMPRESSION = "impression"
    CLICK = "click"


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    SPEND = "spend"


class Advertiser(Base):
    __tablename__ = "advertisers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)
    company_name = Column(String(255), nullable=False)
    balance = Column(Numeric(10, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    ad_campaigns = relationship("AdCampaign", back_populates="advertiser")
    transactions = relationship("Transaction", back_populates="advertiser")


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    advertiser_id = Column(BigInteger, ForeignKey("advertisers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    budget = Column(Numeric(10, 2), nullable=False)
    spent_amount = Column(Numeric(10, 2), default=0.00)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(AdCampaignStatus), default=AdCampaignStatus.DRAFT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    advertiser = relationship("Advertiser", back_populates="ad_campaigns")
    ad_creatives = relationship("AdCreative", back_populates="ad_campaign")
    ad_placements = relationship("AdPlacement", back_populates="ad_campaign")


class AdCreative(Base):
    __tablename__ = "ad_creatives"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id = Column(BigInteger, ForeignKey("ad_campaigns.id"), nullable=False)
    content_type = Column(Enum(AdCreativeContentType), nullable=False)
    text = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)  # Telegram file_id
    url = Column(String(2048), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(AdCreativeStatus), default=AdCreativeStatus.PENDING)
    moderator_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    moderation_comment = Column(Text, nullable=True)

    ad_campaign = relationship("AdCampaign", back_populates="ad_creatives")
    moderator = relationship("User")


class AdPlacement(Base):
    __tablename__ = "ad_placements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id = Column(BigInteger, ForeignKey("ad_campaigns.id"), nullable=False)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False)

    ad_campaign = relationship("AdCampaign", back_populates="ad_placements")
    group = relationship("Group")


class AdAnalytics(Base):
    __tablename__ = "ad_analytics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    creative_id = Column(BigInteger, ForeignKey("ad_creatives.id"), nullable=False)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    event_type = Column(Enum(AdEventType), nullable=False)
    event_time = Column(DateTime(timezone=True), server_default=func.now())

    ad_creative = relationship("AdCreative")
    group = relationship("Group")
    user = relationship("User")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    advertiser_id = Column(BigInteger, ForeignKey("advertisers.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    advertiser = relationship("Advertiser", back_populates="transactions")
