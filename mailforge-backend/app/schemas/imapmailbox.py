from datetime import datetime
from pydantic import BaseModel, EmailStr


class ImapMailboxBase(BaseModel):
    email: EmailStr
    display_name: str | None = None

    imap_host: str
    imap_port: int
    imap_ssl: bool = True

    smtp_host: str
    smtp_port: int
    smtp_tls: bool = True

    username: str
    password: str

    warmup_enabled: bool = False
    is_active: bool = True


class ImapMailboxCreate(ImapMailboxBase):
    pass


class ImapMailboxUpdate(BaseModel):
    display_name: str | None = None
    imap_host: str | None = None
    imap_port: int | None = None
    imap_ssl: bool | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_tls: bool | None = None
    username: str | None = None
    password: str | None = None
    warmup_enabled: bool | None = None
    is_active: bool | None = None


class ImapMailboxOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str | None

    imap_host: str
    imap_port: int
    imap_ssl: bool

    smtp_host: str
    smtp_port: int
    smtp_tls: bool

    warmup_enabled: bool
    is_active: bool

    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True