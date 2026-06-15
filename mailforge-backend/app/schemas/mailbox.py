# app/schemas/mailbox.py

from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class MailboxBase(BaseModel):
    provider: str
    email: EmailStr
    display_name: str | None = None
    warmup_enabled: bool = False


class MailboxOut(MailboxBase):
    id: int
    user_id: int
    oauth_app_id: int | None = None
    last_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    oauth_app_name: str | None = None

    model_config = ConfigDict(from_attributes=True)