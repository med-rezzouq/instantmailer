from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    running = "running"
    completed = "completed"
    paused = "paused"
    outdated = "outdated"
    failed = "failed"


class EmailProvider(str, enum.Enum):
    smtp = "smtp"
    sendgrid = "sendgrid"
    mailgun = "mailgun"
    ses = "ses"
    powermta = "powermta"


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.draft)
    max_bounces = Column(Integer, nullable=True)
    max_complaints = Column(Integer, nullable=True)
    max_unsubscribes = Column(Integer, nullable=True)
    stopped_by_condition = Column(Boolean, default=False, nullable=False)
    stop_reason = Column(String, nullable=True)

    segment_tags = Column("segment_tags", JSON, default=[])
    track_opens = Column("track_opens", Boolean, default=True)
    track_clicks = Column("track_clicks", Boolean, default=True)
    is_followup = Column("is_followup", Boolean, default=False)
    parent_campaign_id = Column("parent_campaign_id", Integer, ForeignKey("campaigns.id"), nullable=True)
    total_contacts = Column("total_contacts", Integer, default=0)
    new_contacts_since_send = Column("new_contacts_since_send", Integer, default=0)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now())
    updated_at = Column("updated_at", DateTime(timezone=True), onupdate=func.now())
    sent_at = Column("sent_at", DateTime(timezone=True), nullable=True)
    scheduled_at = Column("scheduled_at", DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="campaigns")
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")
    steps = relationship("CampaignStep", back_populates="campaign", cascade="all, delete-orphan")
    senders = relationship("CampaignSender", back_populates="campaign", cascade="all, delete-orphan")
    runs = relationship("CampaignRun", back_populates="campaign", cascade="all, delete-orphan")
    contacts = relationship("CampaignContact", back_populates="campaign", cascade="all, delete-orphan")
    events = relationship("CampaignEvent", back_populates="campaign", cascade="all, delete-orphan")


class CampaignRecipient(Base):
    __tablename__ = "campaignrecipients"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column("campaign_id", Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column("contact_id", Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending")
    provider = Column(Enum(EmailProvider), nullable=True)
    sent_at = Column("sent_at", DateTime(timezone=True), nullable=True)
    error = Column(String, nullable=True)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign", back_populates="recipients")