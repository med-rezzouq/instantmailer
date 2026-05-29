from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class CampaignTracking(Base):
    __tablename__ = "campaign_trackings"

    id = Column(Integer, primary_key=True, index=True)

    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)

    action_type = Column(String(20), nullable=False)  # "open" or "click"
    url = Column(String(2048), nullable=True)

    address_ip = Column(String(64), nullable=True)
    country = Column(String(64), nullable=True)
    browser = Column(String(128), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )