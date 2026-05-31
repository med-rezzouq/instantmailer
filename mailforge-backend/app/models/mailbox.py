from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)

    provider = Column(String, nullable=False)      # "google" | "microsoft"
    email = Column(String, nullable=False)
    display_name = Column(String, nullable=True)

    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scope = Column(Text, nullable=True)

    warmup_enabled = Column(Boolean, nullable=False, server_default="false")
    last_sync_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )