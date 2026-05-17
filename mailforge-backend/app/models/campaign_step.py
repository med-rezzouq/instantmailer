from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class StepType(str, enum.Enum):
    initial = "initial"
    followup = "followup"
    reply = "reply"
    post_reply_followup = "post_reply_followup"# followups if they go silent 


class DelayUnit(str, enum.Enum):
    # if you decide not to support seconds, just remove this line
    seconds = "seconds"
    minutes = "minutes"
    hours = "hours"
    days = "days"


class DelayFrom(str, enum.Enum):
    previous_step = "previous_step"
    their_reply = "their_reply"
    our_reply = "our_reply"
    most_recent = "most_recent"


class CampaignStep(Base):
    __tablename__ = "campaign_steps"

    id = Column(Integer, primary_key=True, index=True)

    campaign_id = Column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )

    step_number = Column(Integer, nullable=False)

    step_type = Column(
        Enum(StepType),
        default=StepType.initial,
        nullable=False,
    )

    name = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=True)
    plain_body = Column(Text, nullable=True)

    # main delay: how long to wait after sending THIS step
    delay_value = Column(Integer, default=0, nullable=False)
    delay_unit = Column(
        Enum(DelayUnit),
        default=DelayUnit.days,
        nullable=False,
    )

    delay_from = Column(
        Enum(DelayFrom),
        default=DelayFrom.most_recent,
        nullable=False,
    )

    stop_on_reply = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # NEW: extra delay for reply-type sequences
    # only filled when step_type == StepType.reply_followup
    wait_after_contact_reply_value = Column(Integer, nullable=True)
    wait_after_contact_reply_unit = Column(
        Enum(DelayUnit),
        nullable=True,
    )

    campaign = relationship("Campaign", back_populates="steps")
    events = relationship("CampaignEvent", back_populates="step")