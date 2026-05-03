from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EmailEvent(Base):
    __tablename__ = "email_events"

    id             = Column(Integer, primary_key=True, index=True)
    campaign_id    = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
    contact_id     = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    event_type     = Column(String(50))
    event_metadata = Column("metadata", JSON, nullable=True)
    occurred_at    = Column(DateTime(timezone=True), server_default=func.now())
    ip_address     = Column(String(45))
    user_agent     = Column(String(500))

    campaign = relationship("Campaign", foreign_keys=[campaign_id])
    contact  = relationship("Contact",  foreign_keys=[contact_id])