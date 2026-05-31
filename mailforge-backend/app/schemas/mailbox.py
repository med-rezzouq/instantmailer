# app/schemas/mailbox.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class MailboxBase(BaseModel):
    provider: str           # "google" | "microsoft"
    email: EmailStr
    display_name: Optional[str] = None
    warmup_enabled: bool = False

class MailboxOut(MailboxBase):
    id: int
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True