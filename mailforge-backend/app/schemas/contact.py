from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ContactCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tag_ids: Optional[List[int]] = []

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_subscribed: Optional[bool] = None
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
    model_config = {"from_attributes": True}

class ContactImport(BaseModel):
    contacts: List[ContactCreate]

class TagCreate(BaseModel):
    name: str

class TagOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}
