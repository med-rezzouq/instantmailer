from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


contact_tags = Table(
    "contact_tags",
    Base.metadata,
    Column("contact_id", Integer, ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Contact(Base):
    __tablename__ = "contacts"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email      = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name  = Column(String(100))

    # NEW: required group_id
    group_id   = Column(Integer, ForeignKey("contact_groups.id", ondelete="RESTRICT"), nullable=False)

    is_subscribed = Column(Boolean, default=True)
    open_count    = Column(Integer, default=0)
    click_count   = Column(Integer, default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    user  = relationship("User", back_populates="contacts")
    group = relationship("ContactGroup", back_populates="contacts")
    tags  = relationship("ContactTag", secondary=contact_tags, back_populates="contacts")



class ContactGroup(Base):
    __tablename__ = "contact_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # optional: one-to-many relationship back to contacts
    contacts = relationship("Contact", back_populates="group")



class ContactTag(Base):
    __tablename__ = "tags"

    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String(100), nullable=False)
    user_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    contacts = relationship("Contact", secondary=contact_tags, back_populates="tags")