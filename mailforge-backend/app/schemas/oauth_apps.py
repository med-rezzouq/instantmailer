from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProviderLiteral = Literal["google", "microsoft"]


class OAuthAppBase(BaseModel):
    provider: ProviderLiteral
    name: str = Field(..., min_length=1, max_length=255)
    client_id: str = Field(..., min_length=1)
    redirect_uri: str | None = Field(None, min_length=1)
    scopes: str | None = None
    is_active: bool = True
    owner_email: str | None = None
    project_id: str | None = None


class OAuthAppCreate(OAuthAppBase):
    client_secret: str = Field(..., min_length=1)


class OAuthAppUpdate(BaseModel):
    provider: ProviderLiteral | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    client_id: str | None = Field(None, min_length=1)
    client_secret: str | None = Field(None, min_length=1)
    redirect_uri: str | None = Field(None, min_length=1)
    scopes: str | None = None
    is_active: bool | None = None
    owner_email: str | None = None
    project_id: str | None = None


class OAuthAppOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    provider: ProviderLiteral
    name: str
    client_id: str
    client_secret_masked: str | None = None
    redirect_uri: str | None = None
    scopes: str | None = None
    is_active: bool
    owner_email: str | None = None
    project_id: str | None = None
    created_at: datetime
    updated_at: datetime