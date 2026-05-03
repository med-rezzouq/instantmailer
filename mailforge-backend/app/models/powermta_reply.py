from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class PowerMTAReply(Base):
    __tablename__ = "powermta_replies"
    id            = Column(Integer, primary_key=True, index=True)
    campaign_id   = Column(Integer, nullable=True)
    contact_id    = Column(Integer, nullable=True)
    step_id       = Column(Integer, nullable=True)
    from_email    = Column(String(255))
    to_address    = Column(String(255))
    subject       = Column(String(500))
    body_text     = Column(Text)
    raw_headers   = Column(Text)
    processed     = Column(Boolean, default=False)
    received_at   = Column(DateTime(timezone=True), server_default=func.now())