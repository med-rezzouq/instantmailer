from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SMTPConfigCreate(BaseModel):
    name: str
    host: str
    port: int = 587
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    from_email: Optional[str] = None
    from_name: Optional[str] = None

class SMTPConfigUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    is_active: Optional[bool] = None

class SMTPConfigOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: str
    use_tls: bool
    use_ssl: bool
    from_email: Optional[str]
    from_name: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
