from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name         = Column(String(255), nullable=False)
    category     = Column(String(100))
    html_content = Column(Text, nullable=False)
    thumbnail    = Column(String(500))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="templates")


Template = EmailTemplate