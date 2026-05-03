from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class SenderType(str, enum.Enum):
    smtp    = "smtp"
    google  = "google"
    microsoft = "microsoft"

class CampaignSender(Base):
    __tablename__ = "campaign_senders"
    id            = Column(Integer, primary_key=True, index=True)
    campaign_id   = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
    sender_type   = Column(Enum(SenderType), nullable=False)
    sender_id     = Column(Integer, nullable=False)  # smtp_config.id or oauth_account.id
    sender_label  = Column(String(255))
    quota         = Column(Integer, nullable=False)   # max emails to send via this sender
    sent_count    = Column(Integer, default=0)

    campaign      = relationship("Campaign", back_populates="senders")