from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class ContactStatus(str, enum.Enum):
    active       = "active"
    replied      = "replied"
    completed    = "completed"
    removed      = "removed"
    bounced      = "bounced"
    unsubscribed = "unsubscribed"

class CampaignContact(Base):
    __tablename__ = "campaign_contacts"
    id                  = Column(Integer, primary_key=True, index=True)
    campaign_id         = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
    contact_id          = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    status              = Column(Enum(ContactStatus), default=ContactStatus.active)
    current_step_id     = Column(Integer, ForeignKey("campaign_steps.id"), nullable=True)
    in_reply_thread     = Column(Boolean, default=False)
    reply_step_index    = Column(Integer, default=0)
    last_sent_at        = Column(DateTime(timezone=True), nullable=True)
    replied_at          = Column(DateTime(timezone=True), nullable=True)
    their_last_reply_at = Column(DateTime(timezone=True), nullable=True)
    our_last_sent_at    = Column(DateTime(timezone=True), nullable=True)
    added_at            = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign", back_populates="contacts")
    contact  = relationship("Contact")