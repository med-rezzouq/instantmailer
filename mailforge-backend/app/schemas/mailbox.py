# app/schemas/mailbox.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class MailboxBase(BaseModel):
    provider: str
    email: EmailStr
    display_name: Optional[str] = None
    warmup_enabled: bool = False


class MailboxOut(MailboxBase):
    id: int
    user_id: int
    oauth_app_id: Optional[int] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    oauth_app_name: str | None = None

    class Config:
        from_attributes = True