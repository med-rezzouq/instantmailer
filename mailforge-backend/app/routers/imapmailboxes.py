from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.imap_mailbox import ImapMailbox
from app.schemas.imapmailbox import (
    ImapMailboxCreate,
    ImapMailboxUpdate,
    ImapMailboxOut,
)

router = APIRouter(prefix="/imap-mailboxes", tags=["imap-mailboxes"])


@router.get("", response_model=List[ImapMailboxOut])
async def list_imap_mailboxes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ImapMailbox).where(ImapMailbox.user_id == current_user.id)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=ImapMailboxOut, status_code=status.HTTP_201_CREATED)
async def create_imap_mailbox(
    mailbox_in: ImapMailboxCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mailbox = ImapMailbox(
        user_id=current_user.id,
        **mailbox_in.model_dump(),
    )
    db.add(mailbox)
    await db.commit()
    await db.refresh(mailbox)
    return mailbox


@router.put("/{mailbox_id}", response_model=ImapMailboxOut)
async def update_imap_mailbox(
    mailbox_id: int,
    mailbox_in: ImapMailboxUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ImapMailbox).where(
        ImapMailbox.id == mailbox_id,
        ImapMailbox.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    mailbox = res.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    update_data = mailbox_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(mailbox, k, v)

    await db.commit()
    await db.refresh(mailbox)
    return mailbox


@router.delete("/{mailbox_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_imap_mailbox(
    mailbox_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ImapMailbox).where(
        ImapMailbox.id == mailbox_id,
        ImapMailbox.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    mailbox = res.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    await db.delete(mailbox)
    await db.commit()
    return