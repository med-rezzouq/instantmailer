from datetime import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Enum,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class WarmupDelayUnit(enum.Enum):
    seconds = "seconds"
    minutes = "minutes"
    hours = "hours"


class WarmupTask(Base):
    __tablename__ = "warmup_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    name = Column(String(255), nullable=False)

    # Multiple mailboxes stored as a JSONB array of mailbox IDs, e.g. [1, 2, 3]
    mailbox_ids = Column(JSONB, nullable=False, default=list)

    # Actions to perform during warmup
    do_move_to_inbox = Column(Boolean, nullable=False, default=True)
    do_open = Column(Boolean, nullable=False, default=True)
    do_add_to_favorites = Column(Boolean, nullable=False, default=False)
    do_mark_as_primary = Column(Boolean, nullable=False, default=False)
    do_reply = Column(Boolean, nullable=False, default=True)
    do_campaign_reply = Column(Boolean, nullable=False, default=False)
    reply_message = Column(String(2000), nullable=True)

    # General delay between actions
    delay_seconds = Column(Integer, nullable=False, default=60)
    delay_unit = Column(
        Enum(WarmupDelayUnit, name="warmupdelayunit"),
        nullable=False,
        default=WarmupDelayUnit.seconds,
    )

    # Email address to filter warmup messages by (optional)
    allowed_sender = Column(String(255), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

