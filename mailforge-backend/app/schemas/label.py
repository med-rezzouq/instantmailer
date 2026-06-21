from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LabelBase(BaseModel):
    name: str
    description: str | None = None


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class LabelOut(LabelBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)