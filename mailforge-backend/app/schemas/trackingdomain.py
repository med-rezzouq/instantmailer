from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, AnyHttpUrl, field_validator


class TrackingDomainBase(BaseModel):
    domain: AnyHttpUrl

    @field_validator("domain")
    @classmethod
    def enforce_https(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        if v.scheme != "https":
            raise ValueError("Tracking domain must use https://")
        return v


class TrackingDomainCreate(TrackingDomainBase):
    pass


class TrackingDomainUpdate(TrackingDomainBase):
    pass


class TrackingDomainOut(TrackingDomainBase):
    id: int
    campaign_ids: Optional[List[int]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True