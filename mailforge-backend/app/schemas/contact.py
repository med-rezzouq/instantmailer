from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class ContactCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    group_id: int
    is_system: bool = False


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_subscribed: Optional[bool] = None
    group_id: Optional[int] = None
    is_system: Optional[bool] = None


class ContactOut(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_system: bool
    is_subscribed: bool
    open_count: int
    click_count: int
    created_at: datetime
    group_id: int

    model_config = ConfigDict(from_attributes=True)


class ContactImportItem(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    group_id: int
    is_system: bool = False


class ContactImport(BaseModel):
    contacts: List[ContactImportItem]


class TagCreate(BaseModel):
    name: str


class TagOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ContactGroupBase(BaseModel):
    name: str
    is_system: bool = False


class ContactGroupCreate(ContactGroupBase):
    pass


class ContactGroupUpdate(ContactGroupBase):
    pass


class ContactGroupOut(ContactGroupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)