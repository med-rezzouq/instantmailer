from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.campaign import CampaignStatus
from app.models.campaign_step import StepType, DelayUnit, DelayFrom


class CampaignStepBase(BaseModel):
    step_number: int = Field(..., ge=1)
    step_type: StepType = StepType.initial
    name: Optional[str] = None
    subject: str
    html_body: Optional[str] = None
    plain_body: Optional[str] = None
    delay_value: int = Field(0, ge=0)
    delay_unit: DelayUnit = DelayUnit.days
    delay_from: DelayFrom = DelayFrom.most_recent
    stop_on_reply: bool = True
    is_active: bool = True

    # NEW: only used for reply_followup steps
    wait_after_contact_reply_value: Optional[int] = Field(None, ge=0)
    wait_after_contact_reply_unit: Optional[DelayUnit] = None

    @model_validator(mode="after")
    def validate_step_rules(self):
        if self.step_type == StepType.initial:
            if self.step_number != 1:
                raise ValueError("Initial step must have step_number = 1")
            if self.delay_value != 0:
                raise ValueError("Initial step must have delay_value = 0")
        else:
            if self.delay_value < 1:
                raise ValueError("Non-initial steps must have delay_value >= 1")

        if self.step_type in (StepType.reply, StepType.post_reply_followup):
            if self.delay_from == DelayFrom.previous_step:
                raise ValueError(
                    "Reply-related steps cannot use delay_from='previous_step'; "
                    "use their_reply, our_reply, or most_recent"
                )
            # optional: enforce that reply steps have contact-reply delay set
            # if self.wait_after_contact_reply_value is None:
            #     raise ValueError("reply_followup steps must define wait_after_contact_reply_value")
            # if self.wait_after_contact_reply_unit is None:
            #     raise ValueError("reply_followup steps must define wait_after_contact_reply_unit")

        return self


class CampaignStepCreate(CampaignStepBase):
    pass


class CampaignStepUpdate(BaseModel):
    id: Optional[int] = None
    step_number: Optional[int] = Field(None, ge=1)
    step_type: Optional[StepType] = None
    name: Optional[str] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    plain_body: Optional[str] = None
    delay_value: Optional[int] = Field(None, ge=0)
    delay_unit: Optional[DelayUnit] = None
    delay_from: Optional[DelayFrom] = None
    stop_on_reply: Optional[bool] = None
    is_active: Optional[bool] = None
    # NEW
    wait_after_contact_reply_value: Optional[int] = Field(None, ge=0)
    wait_after_contact_reply_unit: Optional[DelayUnit] = None

class CampaignStepOut(CampaignStepBase):
    id: int
    campaign_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class InboundReplyIn(BaseModel):
    from_email: str
    to_email: str
    subject: Optional[str] = None
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    occurred_at: Optional[datetime] = None

    # NEW: simulated data from headers / message-id lookup
    step_id: Optional[int] = None
    step_number: Optional[int] = None
    
class CampaignCreate(BaseModel):
    name: str
    preview_text: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    segment_tags: List[str] = Field(default_factory=list)
    track_opens: bool = True
    track_clicks: bool = True
    is_followup: bool = False
    parent_campaign_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None

    # NEW: selected SMTP provider for this campaign
    provider_id: Optional[int] = None

    max_bounces: Optional[int] = None
    max_complaints: Optional[int] = None
    max_unsubscribes: Optional[int] = None
    max_followups: Optional[int] = None
    general_warmup_delay_value: int = 10
    general_warmup_delay_unit: DelayUnit = DelayUnit.minutes

    steps: List[CampaignStepCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_steps(self):
        if not self.steps:
            return self

        step_numbers = [step.step_number for step in self.steps]
        if len(step_numbers) != len(set(step_numbers)):
            raise ValueError("Step numbers must be unique")

        sorted_steps = sorted(self.steps, key=lambda s: s.step_number)

        initial_steps = [step for step in sorted_steps if step.step_type == StepType.initial]
        if len(initial_steps) != 1:
            raise ValueError("Campaign must contain exactly one initial step")

        if sorted_steps[0].step_type != StepType.initial:
            raise ValueError("The first step in the campaign must be the initial step")

        if sorted_steps[0].step_number != 1:
            raise ValueError("The first step must have step_number = 1")

        for step in sorted_steps[1:]:
            if step.step_type == StepType.initial:
                raise ValueError("Only one step can have step_type='initial'")

        return self


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    preview_text: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    status: Optional[CampaignStatus] = None
    segment_tags: Optional[List[str]] = None
    track_opens: Optional[bool] = None
    track_clicks: Optional[bool] = None
    is_followup: Optional[bool] = None
    parent_campaign_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None

    # NEW: allow changing provider for an existing campaign
    provider_id: Optional[int] = None

    max_bounces: Optional[int] = None
    max_complaints: Optional[int] = None
    max_unsubscribes: Optional[int] = None
    max_followups: Optional[int] = None
    general_warmup_delay_value: Optional[int] = None
    general_warmup_delay_unit: Optional[DelayUnit] = None
    steps: Optional[List[CampaignStepCreate]] = None

    @model_validator(mode="after")
    def validate_steps(self):
        if self.steps is None:
            return self

        if not self.steps:
            raise ValueError("If steps is provided, it must contain at least one step")

        step_numbers = [step.step_number for step in self.steps]
        if len(step_numbers) != len(set(step_numbers)):
            raise ValueError("Step numbers must be unique")

        sorted_steps = sorted(self.steps, key=lambda s: s.step_number)

        initial_steps = [step for step in sorted_steps if step.step_type == StepType.initial]
        if len(initial_steps) != 1:
            raise ValueError("Campaign steps must contain exactly one initial step")

        if sorted_steps[0].step_type != StepType.initial:
            raise ValueError("The first step in the campaign must be the initial step")

        if sorted_steps[0].step_number != 1:
            raise ValueError("The first step must have step_number = 1")

        for step in sorted_steps[1:]:
            if step.step_type == StepType.initial:
                raise ValueError("Only one step can have step_type='initial'")

        return self


class CampaignOut(BaseModel):
    id: int
    user_id: int
    name: str
    status: CampaignStatus
    preview_text: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None

    # NEW: expose chosen SMTP provider to frontend
    provider_id: Optional[int] = None

    segment_tags: List[str] = Field(default_factory=list)
    track_opens: bool
    track_clicks: bool
    is_followup: bool
    parent_campaign_id: Optional[int] = None
    max_bounces: Optional[int] = 0
    max_complaints: Optional[int] = None
    max_unsubscribes: Optional[int] = None
    max_followups: Optional[int] = None
    stopped_by_condition: bool = False
    stop_reason: Optional[str] = None

    total_contacts: int
    new_contacts_since_send: int

    created_at: datetime
    updated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    # NEW: warm-up config returned to frontend
    general_warmup_delay_value: int
    general_warmup_delay_unit: DelayUnit
    # temporary compatibility fields for frontend
    subject: Optional[str] = None
    html_content: Optional[str] = None
    plain_content: Optional[str] = None
    followup_count: int = 0

    steps: List[CampaignStepOut] = Field(default_factory=list)
    
    model_config = {"from_attributes": True}


