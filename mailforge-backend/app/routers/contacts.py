from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.contact import Contact, ContactGroup
from app.models.user import User
from app.schemas.contact import (
    ContactCreate,
    ContactGroupCreate,
    ContactGroupOut,
    ContactGroupUpdate,
    ContactImport,
    ContactOut,
    ContactUpdate,
)

router = APIRouter(prefix="/contacts", tags=["Contacts"])


async def _get_user_group(
    db: AsyncSession,
    user_id: int,
    group_id: int,
) -> ContactGroup | None:
    result = await db.execute(
        select(ContactGroup).where(
            ContactGroup.id == group_id,
            ContactGroup.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def _email_exists_for_user_in_group(
    db: AsyncSession,
    user_id: int,
    email: str,
    group_id: int,
    exclude_contact_id: Optional[int] = None,
) -> bool:
    q = select(Contact.id).where(
        Contact.user_id == user_id,
        Contact.group_id == group_id,
        func.lower(Contact.email) == email.lower(),
    )

    if exclude_contact_id is not None:
        q = q.where(Contact.id != exclude_contact_id)

    result = await db.execute(q.limit(1))
    return result.scalar_one_or_none() is not None


async def _email_marked_bounce(
    db: AsyncSession,
    email: str,
) -> bool:
    result = await db.execute(
        select(Contact.id)
        .join(ContactGroup, Contact.group_id == ContactGroup.id)
        .where(
            func.lower(Contact.email) == email.lower(),
            func.lower(ContactGroup.name) == "bounces",
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


# ── Groups ────────────────────────────────────────────────────────────────

@router.get("/groups", response_model=List[ContactGroupOut])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContactGroup)
        .where(ContactGroup.user_id == current_user.id)
        .order_by(ContactGroup.is_system.asc(), ContactGroup.name.asc())
    )
    return result.scalars().all()


@router.post("/groups", response_model=ContactGroupOut, status_code=201)
async def create_group(
    payload: ContactGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")

    existing = await db.execute(
        select(ContactGroup).where(
            ContactGroup.user_id == current_user.id,
            ContactGroup.name == name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group with this name already exists")

    group = ContactGroup(
        name=name,
        user_id=current_user.id,
        is_system=payload.is_system,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.put("/groups/{group_id}", response_model=ContactGroupOut)
async def update_group(
    group_id: int,
    payload: ContactGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await db.get(ContactGroup, group_id)
    if not group or group.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Group not found")

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")

    existing = await db.execute(
        select(ContactGroup).where(
            ContactGroup.user_id == current_user.id,
            ContactGroup.name == name,
            ContactGroup.id != group_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group with this name already exists")

    group.name = name
    group.is_system = payload.is_system

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await db.get(ContactGroup, group_id)
    if not group or group.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.is_system:
        raise HTTPException(status_code=400, detail="System groups cannot be deleted")

    await db.delete(group)
    await db.commit()
    return {"ok": True}


# ── Contacts ──────────────────────────────────────────────────────────────

@router.get("", response_model=List[ContactOut])
async def list_contacts(
    search: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Contact).where(Contact.user_id == current_user.id)

    if search:
        q = q.where(
            or_(
                Contact.email.ilike(f"%{search}%"),
                Contact.first_name.ilike(f"%{search}%"),
                Contact.last_name.ilike(f"%{search}%"),
            )
        )

    if group_id is not None:
        q = q.where(Contact.group_id == group_id)

    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=ContactOut, status_code=201)
async def create_contact(
    payload: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    email = payload.email.strip().lower()

    group = await _get_user_group(db, current_user.id, payload.group_id)
    if not group:
        raise HTTPException(status_code=400, detail="Invalid group_id")

    if await _email_exists_for_user_in_group(
        db,
        current_user.id,
        email,
        payload.group_id,
    ):
        raise HTTPException(
            status_code=400,
            detail="Contact with this email already exists in this group",
        )

    if await _email_marked_bounce(db, email):
        raise HTTPException(
            status_code=400,
            detail="can't add this contact its marked bounce in our systems",
        )

    contact = Contact(
        user_id=current_user.id,
        email=email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        group_id=payload.group_id,
        is_system=bool(group.is_system),
    )

    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")

    data = payload.model_dump(exclude_unset=True)
    group_id = data.pop("group_id", None)

    for field, value in data.items():
        setattr(contact, field, value)

    if group_id is not None:
        group = await _get_user_group(db, current_user.id, group_id)
        if not group:
            raise HTTPException(status_code=400, detail="Invalid group_id")
        contact.group_id = group_id
        if group.is_system:
            contact.is_system = True

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

    if contact.is_system:
        raise HTTPException(status_code=400, detail="Protected contacts cannot be deleted")

    group = await _get_user_group(db, current_user.id, contact.group_id)
    if group and group.is_system:
        raise HTTPException(status_code=400, detail="Contacts in system groups cannot be deleted")

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
        email = c.email.strip().lower()

        group = await _get_user_group(db, current_user.id, c.group_id)
        if not group:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group_id for contact {c.email}",
            )

        if await _email_exists_for_user_in_group(
            db,
            current_user.id,
            email,
            c.group_id,
        ):
            skipped += 1
            continue

        if await _email_marked_bounce(db, email):
            skipped += 1
            continue

        db.add(
            Contact(
                user_id=current_user.id,
                email=email,
                first_name=c.first_name,
                last_name=c.last_name,
                group_id=c.group_id,
                is_system=bool(group.is_system),
            )
        )
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped}