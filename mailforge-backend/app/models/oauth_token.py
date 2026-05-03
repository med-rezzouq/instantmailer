from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class OAuthProvider(str, enum.Enum):
    MICROSOFT = "microsoft"
    GOOGLE    = "google"

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    provider      = Column(Enum(OAuthProvider), nullable=False)
    access_token  = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_expiry  = Column(DateTime(timezone=True))
    scope         = Column(String(500))
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="oauth_tokens")
