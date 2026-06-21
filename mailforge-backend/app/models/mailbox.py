# app/models/mailbox.py

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func
from app.database import Base


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    oauth_app_id = Column(Integer, ForeignKey("oauth_apps.id", ondelete="SET NULL"), nullable=True, index=True)

    provider = Column(String(50), nullable=False, default="custom")
    access_protocol = Column(String(20), nullable=False, default="oauth2")

    email = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)

    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)

    imap_host = Column(String(255), nullable=True)
    imap_port = Column(Integer, nullable=True)
    imap_ssl = Column(Boolean, nullable=False, default=True)

    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_tls = Column(Boolean, nullable=False, default=True)

    username = Column(String(255), nullable=True)
    password = Column(Text, nullable=True)

    warmup_enabled = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)