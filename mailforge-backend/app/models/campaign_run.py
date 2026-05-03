from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class RunStatus(str, enum.Enum):
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"
    paused    = "paused"

class CampaignRun(Base):
    __tablename__ = "campaign_runs"
    id           = Column(Integer, primary_key=True, index=True)
    campaign_id  = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
    step_id      = Column(Integer, ForeignKey("campaign_steps.id", ondelete="SET NULL"), nullable=True)
    status       = Column(Enum(RunStatus), default=RunStatus.pending)
    total_sent   = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    started_at   = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_log    = Column(Text, nullable=True)

    campaign = relationship("Campaign", back_populates="runs")