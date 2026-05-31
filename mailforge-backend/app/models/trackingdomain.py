from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TrackingDomain(Base):
    __tablename__ = "tracking_domains"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Full URL, e.g. "https://track.example.com"
    domain = Column(String(255), nullable=False, unique=True)

    # For now just a JSON array of integers (campaign ids), nullable
    campaign_ids = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="tracking_domains")