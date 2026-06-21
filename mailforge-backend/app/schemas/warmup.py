from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator


class WarmupDelayUnit(str, Enum):
    seconds = "seconds"
    minutes = "minutes"
    hours = "hours"


class WarmupTaskProtocol(str, Enum):
    oauth = "oauth"
    imap = "imap"


class WarmupTaskBase(BaseModel):
    name: str
    mailbox_ids: list[int]

    protocol: WarmupTaskProtocol = WarmupTaskProtocol.oauth

    do_move_to_inbox: bool = True
    do_open: bool = True
    do_add_to_favorites: bool = False
    do_mark_as_primary: bool = False
    do_reply: bool = True
    do_campaign_reply: bool = False
    do_detect_reply_event: bool = False
    reply_message: str | None = None

    delay_seconds: int = 60
    delay_unit: WarmupDelayUnit = WarmupDelayUnit.seconds

    allowed_sender: str | None = None
    is_active: bool = True


class WarmupTaskCreate(WarmupTaskBase):
    oauth_app_id: int | None = None

    @model_validator(mode="after")
    def validate_create_rules(self):
        if self.protocol == WarmupTaskProtocol.oauth and not self.oauth_app_id:
            raise ValueError("oauth_app_id is required for OAuth warmup tasks")

        if self.protocol == WarmupTaskProtocol.imap:
            if self.do_mark_as_primary:
                raise ValueError("do_mark_as_primary is not supported for IMAP warmup tasks")
            if self.do_reply:
                raise ValueError("do_reply is not supported for IMAP warmup tasks")
            if self.do_campaign_reply:
                raise ValueError("do_campaign_reply is not supported for IMAP warmup tasks")
            if self.reply_message:
                raise ValueError("reply_message must be empty for IMAP warmup tasks")

        return self


class WarmupTaskUpdate(BaseModel):
    name: str | None = None
    mailbox_ids: list[int] | None = None

    protocol: WarmupTaskProtocol | None = None
    oauth_app_id: int | None = None

    do_move_to_inbox: bool | None = None
    do_open: bool | None = None
    do_add_to_favorites: bool | None = None
    do_mark_as_primary: bool | None = None
    do_reply: bool | None = None
    do_campaign_reply: bool | None = None
    do_detect_reply_event: bool | None = None
    reply_message: str | None = None

    delay_seconds: int | None = None
    delay_unit: WarmupDelayUnit | None = None

    allowed_sender: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_update_rules(self):
        effective_protocol = self.protocol

        if effective_protocol == WarmupTaskProtocol.oauth and self.oauth_app_id is None:
            pass

        if effective_protocol == WarmupTaskProtocol.imap:
            if self.do_mark_as_primary is True:
                raise ValueError("do_mark_as_primary is not supported for IMAP warmup tasks")
            if self.do_reply is True:
                raise ValueError("do_reply is not supported for IMAP warmup tasks")
            if self.do_campaign_reply is True:
                raise ValueError("do_campaign_reply is not supported for IMAP warmup tasks")
            if self.reply_message not in (None, ""):
                raise ValueError("reply_message must be empty for IMAP warmup tasks")

        return self


class WarmupTaskOut(BaseModel):
    id: int
    user_id: int
    name: str
    protocol: WarmupTaskProtocol
    oauth_app_id: int | None
    oauth_app_name: str | None = None
    oauth_app_provider: str | None = None
    mailbox_ids: list[int]

    do_move_to_inbox: bool
    do_open: bool
    do_add_to_favorites: bool
    do_mark_as_primary: bool
    do_reply: bool
    do_campaign_reply: bool
    do_detect_reply_event: bool
    reply_message: str | None

    delay_seconds: int
    delay_unit: WarmupDelayUnit

    allowed_sender: str | None
    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarmupPerformIn(BaseModel):
    delay_time: int | None = None
    sender_email: str | None = None


class WarmupPerformOut(BaseModel):
    ok: bool = True
    mailbox_id: int
    action: str | None = None
    detail: str | None = None
    runid: str | None = None


class WarmupEventItemOut(BaseModel):
    id: int
    warmup_task_id: int
    mailbox_id: int
    action: str | None = None
    status: str | None = None
    detail: str | None = None
    target_value: str | None = None
    runid: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarmupRunGroupOut(BaseModel):
    runid: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: int | None = None
    status: str | None = None
    events: list[WarmupEventItemOut]


class WarmupTaskRunViewOut(BaseModel):
    task_id: int
    runs: list[WarmupRunGroupOut]