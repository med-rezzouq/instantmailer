from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ImapMailbox(Base):
    __tablename__ = "imap_mailboxes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)

    # Basic identity
    email = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)

    # IMAP settings
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, nullable=False, default=993)
    imap_ssl = Column(Boolean, nullable=False, default=True)

    # SMTP settings
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_tls = Column(Boolean, nullable=False, default=True)

    # Auth
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)  # later: encrypt / external vault

    # Flags
    warmup_enabled = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Meta
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )