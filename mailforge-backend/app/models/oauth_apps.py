from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class OAuthApp(Base):
    __tablename__ = "oauth_apps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    provider = Column(String(50), nullable=False, index=True)  # "google" | "microsoft"
    name = Column(String(255), nullable=False)

    client_id = Column(Text, nullable=False)
    client_secret = Column(Text, nullable=False)  # later you can encrypt this
    redirect_uri = Column(Text, nullable=False)
    scopes = Column(Text, nullable=True)
    owner_email = Column(String(255), nullable=True, index=True)
    project_id = Column(String(255), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    