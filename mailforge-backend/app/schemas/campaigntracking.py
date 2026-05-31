from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, AnyUrl


class CampaignTrackingBase(BaseModel):
    action_type: Literal["open", "click"]
    campaign_id: int
    contact_id: int
    url: Optional[AnyUrl] = None
    address_ip: Optional[str] = None
    country: Optional[str] = None
    browser: Optional[str] = None


class CampaignTrackingCreate(CampaignTrackingBase):
    pass


class CampaignTrackingOut(CampaignTrackingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True