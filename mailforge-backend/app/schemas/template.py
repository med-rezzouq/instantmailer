from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TemplateCreate(BaseModel):
    name: str
    category: Optional[str] = None
    html_content: str

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    html_content: Optional[str] = None

class TemplateOut(BaseModel):
    id: int
    name: str
    category: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
