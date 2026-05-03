from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.contact import Contact, ContactTag
from app.schemas.contact import ContactCreate, ContactUpdate, ContactOut, ContactImport, TagCreate, TagOut
from app.dependencies import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.get("", response_model=List[ContactOut])
async def list_contacts(
    search: Optional[str] = Query(None),
    tag_id: Optional[int] = Query(None),
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Contact).where(Contact.user_id == current_user.id)
    if search:
        q = q.where(or_(Contact.email.ilike(f"%{search}%"),
                        Contact.first_name.ilike(f"%{search}%"),
                        Contact.last_name.ilike(f"%{search}%")))
    if tag_id:
        from app.models.contact import contact_tags
        q = q.join(contact_tags).where(contact_tags.c.tag_id == tag_id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()

@router.post("", response_model=ContactOut, status_code=201)
async def create_contact(
    payload: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(Contact).where(Contact.user_id == current_user.id, Contact.email == payload.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Contact with this email already exists")
    contact = Contact(user_id=current_user.id, email=payload.email,
                      first_name=payload.first_name, last_name=payload.last_name)
    if payload.tag_ids:
        tags_result = await db.execute(select(ContactTag).where(ContactTag.id.in_(payload.tag_ids)))
        contact.tags = tags_result.scalars().all()
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: int, payload: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in payload.model_dump(exclude_unset=True, exclude={"tag_ids"}).items():
        setattr(contact, field, value)
    if payload.tag_ids is not None:
        tags_result = await db.execute(select(ContactTag).where(ContactTag.id.in_(payload.tag_ids)))
        contact.tags = tags_result.scalars().all()
    await db.commit()
    await db.refresh(contact)
    return contact

@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)
    await db.commit()

@router.post("/import", status_code=201)
async def import_contacts(
    payload: ContactImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = 0
    skipped = 0
    for c in payload.contacts:
        existing = await db.execute(
            select(Contact).where(Contact.user_id == current_user.id, Contact.email == c.email)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        db.add(Contact(user_id=current_user.id, email=c.email,
                       first_name=c.first_name, last_name=c.last_name))
        created += 1
    await db.commit()
    return {"created": created, "skipped": skipped}

# ── Tags ──────────────────────────────────────────────────────────────────
@router.get("/tags", response_model=List[TagOut])
async def list_tags(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ContactTag).where(ContactTag.user_id == current_user.id))
    return result.scalars().all()

@router.post("/tags", response_model=TagOut, status_code=201)
async def create_tag(
    payload: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = ContactTag(name=payload.name, user_id=current_user.id)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag