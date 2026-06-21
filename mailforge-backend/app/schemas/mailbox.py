from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class MailboxImapCreate(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    imap_host: str
    imap_port: int
    imap_ssl: bool = True
    smtp_host: str
    smtp_port: int
    smtp_tls: bool = True
    username: str
    password: str
    warmup_enabled: bool = True
    is_active: bool = True


class MailboxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    provider: str
    access_protocol: str
    email: EmailStr
    display_name: Optional[str] = None
    warmup_enabled: bool
    is_active: bool = True
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    oauth_app_id: Optional[int] = None
    oauth_app_name: Optional[str] = None

    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_ssl: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_tls: Optional[bool] = None
    username: Optional[str] = None


    