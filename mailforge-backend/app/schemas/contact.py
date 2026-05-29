from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ContactCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    group_id: int  # REQUIRED: which group/list this contact belongs to
    tag_ids: Optional[List[int]] = []

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_subscribed: Optional[bool] = None
    group_id: Optional[int] = None  # allow moving contact to a different group
    tag_ids: Optional[List[int]] = None

class ContactOut(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_subscribed: bool
    open_count: int
    click_count: int
    created_at: datetime
    group_id: int  # so frontend knows which list it belongs to
    model_config = {"from_attributes": True}

class ContactImport(BaseModel):
    contacts: List[ContactCreate]

class TagCreate(BaseModel):
    name: str

class TagOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class ContactGroupBase(BaseModel):
    name: str


class ContactGroupCreate(ContactGroupBase):
    pass


class ContactGroupUpdate(ContactGroupBase):
    pass


class ContactGroupOut(ContactGroupBase):
    id: int

    class Config:
        from_attributes = True