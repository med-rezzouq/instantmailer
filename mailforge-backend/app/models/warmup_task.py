from datetime import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Enum,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class WarmupDelayUnit(enum.Enum):
    seconds = "seconds"
    minutes = "minutes"
    hours = "hours"


class WarmupTaskProtocol(enum.Enum):
    oauth = "oauth"
    imap = "imap"


class WarmupTask(Base):
    __tablename__ = "warmup_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    name = Column(String(255), nullable=False)

    protocol = Column(
        Enum(WarmupTaskProtocol, name="warmuptaskprotocol"),
        nullable=False,
        default=WarmupTaskProtocol.oauth,
    )

    oauth_app_id = Column(
        Integer,
        ForeignKey("oauth_apps.id"),
        nullable=True,
        index=True,
    )

    oauth_app = relationship("OAuthApp")

    mailbox_ids = Column(JSONB, nullable=False, default=list)

    do_move_to_inbox = Column(Boolean, nullable=False, default=True)
    do_open = Column(Boolean, nullable=False, default=True)
    do_add_to_favorites = Column(Boolean, nullable=False, default=False)
    do_mark_as_primary = Column(Boolean, nullable=False, default=False)
    do_reply = Column(Boolean, nullable=False, default=True)
    do_campaign_reply = Column(Boolean, nullable=False, default=False)
    do_detect_reply_event = Column(Boolean, nullable=False, default=False)
    reply_message = Column(String(2000), nullable=True)

    delay_seconds = Column(Integer, nullable=False, default=60)
    delay_unit = Column(
        Enum(WarmupDelayUnit, name="warmupdelayunit"),
        nullable=False,
        default=WarmupDelayUnit.seconds,
    )

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