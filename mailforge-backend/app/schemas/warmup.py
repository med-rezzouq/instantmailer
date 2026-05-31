from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class WarmupDelayUnit(str, Enum):
    seconds = "seconds"
    minutes = "minutes"
    hours = "hours"


class WarmupTaskBase(BaseModel):
    name: str

    # Multiple mailbox IDs, stored in JSONB column mailbox_ids
    mailbox_ids: list[int]

    do_move_to_inbox: bool = True
    do_open: bool = True
    do_add_to_favorites: bool = False
    do_add_to_contacts: bool = False
    do_reply: bool = True
    do_campaign_reply: bool = False
    reply_message: str | None = None

    delay_seconds: int = 60
    delay_unit: WarmupDelayUnit = WarmupDelayUnit.seconds

    # Email address filter, optional
    allowed_sender: str | None = None

    is_active: bool = True


class WarmupTaskCreate(WarmupTaskBase):
    pass


class WarmupTaskUpdate(BaseModel):
    name: str | None = None
    mailbox_ids: list[int] | None = None

    do_move_to_inbox: bool | None = None
    do_open: bool | None = None
    do_add_to_favorites: bool | None = None
    do_add_to_contacts: bool | None = None
    do_reply: bool | None = None
    do_campaign_reply: bool | None = None
    reply_message: str | None = None

    delay_seconds: int | None = None
    delay_unit: WarmupDelayUnit | None = None

    allowed_sender: str | None = None
    is_active: bool | None = None


class WarmupTaskOut(BaseModel):
    id: int
    user_id: int
    name: str

    mailbox_ids: list[int]

    do_move_to_inbox: bool
    do_open: bool
    do_add_to_favorites: bool
    do_add_to_contacts: bool
    do_reply: bool
    do_campaign_reply: bool
    reply_message: str | None

    delay_seconds: int
    delay_unit: WarmupDelayUnit

    allowed_sender: str | None
    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True