# app/models/warmup_event.py

import enum

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, String, Text
from sqlalchemy.sql import func

from app.database import Base


class WarmupAction(enum.Enum):
    open = "open"
    move_to_inbox = "move_to_inbox"
    add_to_favorites = "add_to_favorites"
    mark_as_primary = "mark_as_primary"
    reply = "reply"


class WarmupEventStatus(enum.Enum):
    started = "started"
    running = "running"
    finished = "finished"
    finished_with_error = "finished_with_error"


class WarmupEvent(Base):
    __tablename__ = "warmup_events"

    id = Column(Integer, primary_key=True, index=True)

    warmup_task_id = Column(
        Integer,
        ForeignKey("warmup_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mailbox_id = Column(
        Integer,
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action = Column(
        Enum(WarmupAction, name="warmupaction"),
        nullable=True,
    )

    status = Column(
        Enum(WarmupEventStatus, name="warmupeventstatus"),
        nullable=True,
        index=True,
    )

    detail = Column(
        Text,
        nullable=True,
    )

    target_value = Column(
        String,
        nullable=True,
    )

    runid = Column(
        String(64),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )