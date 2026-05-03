from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class EventType(str, enum.Enum):
    sent        = "sent"
    open        = "open"
    click       = "click"
    reply       = "reply"
    bounce      = "bounce"
    spam        = "spam"
    unsubscribe = "unsubscribe"

class CampaignEvent(Base):
    __tablename__ = "campaign_events"
    id          = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
    step_id     = Column(Integer, ForeignKey("campaign_steps.id", ondelete="SET NULL"), nullable=True)
    contact_id  = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    event_type  = Column(Enum(EventType), nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_   = Column("metadata", JSON, default={})

    campaign = relationship("Campaign", back_populates="events")
    step     = relationship("CampaignStep", back_populates="events")