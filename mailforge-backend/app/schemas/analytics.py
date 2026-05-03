from pydantic import BaseModel
from typing import List
from datetime import datetime

class CampaignStats(BaseModel):
    campaign_id: int
    campaign_name: str
    total_sent: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    open_rate: float
    click_rate: float
    bounce_rate: float

class DashboardStats(BaseModel):
    total_campaigns: int
    total_contacts: int
    total_emails_sent: int
    avg_open_rate: float
    avg_click_rate: float

class EventOut(BaseModel):
    id: int
    event_type: str
    occurred_at: datetime
    model_config = {"from_attributes": True}
