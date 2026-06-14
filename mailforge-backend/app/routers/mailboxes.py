# app/routers/mailboxes.py

from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlencode
import base64
import json
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.mailbox import Mailbox
from app.models.oauth_apps import OAuthApp
from app.schemas.mailbox import MailboxOut


GOOGLE_APP_MAX_MAILBOXES = int(os.getenv("GOOGLE_APP_MAX_MAILBOXES", "10"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "").rstrip("/")

if not FRONTEND_URL:
    raise RuntimeError("FRONTEND_URL is not configured")

GOOGLE_REDIRECT_URI = f"{FRONTEND_URL}/mailboxes/oauth/google/callback"
MICROSOFT_REDIRECT_URI = f"{FRONTEND_URL}/mailboxes/oauth/microsoft/callback"

router = APIRouter(prefix="/mailboxes", tags=["mailboxes"])


def encode_state(data: dict) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_state(value: str) -> dict:
    try:
        raw = base64.urlsafe_b64decode(value.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state")


async def get_available_google_oauth_app(
    db: AsyncSession,
    user_id: int,
) -> OAuthApp | None:
    stmt = (
        select(
            OAuthApp,
            func.count(Mailbox.id).label("mailbox_count"),
        )
        .outerjoin(Mailbox, Mailbox.oauth_app_id == OAuthApp.id)
        .where(
            OAuthApp.user_id == user_id,
            OAuthApp.provider == "google",
            OAuthApp.is_active.is_(True),
        )
        .group_by(OAuthApp.id)
        .order_by(OAuthApp.created_at.asc(), OAuthApp.id.asc())
    )

    res = await db.execute(stmt)
    rows = res.all()

    for oauth_app, mailbox_count in rows:
        if mailbox_count < GOOGLE_APP_MAX_MAILBOXES:
            return oauth_app

    return None


async def revoke_google_mailbox_access(mailbox: Mailbox) -> None:
    token_to_revoke = mailbox.refresh_token or mailbox.access_token
    if not token_to_revoke:
        return

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token_to_revoke},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if res.status_code not in (200, 400):
        raise HTTPException(
            status_code=400,
            detail=f"Failed to revoke Google mailbox access: {res.text}",
        )


@router.get("", response_model=List[MailboxOut])
async def list_mailboxes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Mailbox, OAuthApp.name.label("oauth_app_name"))
        .outerjoin(OAuthApp, OAuthApp.id == Mailbox.oauth_app_id)
        .where(Mailbox.user_id == current_user.id)
        .order_by(Mailbox.created_at.desc(), Mailbox.id.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
        MailboxOut(
            id=mailbox.id,
            user_id=mailbox.user_id,
            provider=mailbox.provider,
            email=mailbox.email,
            display_name=mailbox.display_name,
            warmup_enabled=mailbox.warmup_enabled,
            last_sync_at=mailbox.last_sync_at,
            created_at=mailbox.created_at,
            updated_at=mailbox.updated_at,
            oauth_app_name=oauth_app_name,
        )
        for mailbox, oauth_app_name in rows
    ]

@router.get("/warmup-options", response_model=List[MailboxOut])
async def list_warmup_mailboxes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Mailbox, OAuthApp.name.label("oauth_app_name"))
        .outerjoin(OAuthApp, OAuthApp.id == Mailbox.oauth_app_id)
        .where(
            Mailbox.user_id == current_user.id,
            Mailbox.warmup_enabled.is_(True),
        )
        .order_by(Mailbox.email.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
        MailboxOut(
            id=mailbox.id,
            user_id=mailbox.user_id,
            provider=mailbox.provider,
            email=mailbox.email,
            display_name=mailbox.display_name,
            warmup_enabled=mailbox.warmup_enabled,
            last_sync_at=mailbox.last_sync_at,
            created_at=mailbox.created_at,
            updated_at=mailbox.updated_at,
            oauth_app_name=oauth_app_name,
        )
        for mailbox, oauth_app_name in rows
    ]




    
@router.get("/connect/google")
async def connect_google(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    oauth_app = await get_available_google_oauth_app(db, current_user.id)

    if not oauth_app:
        raise HTTPException(
            status_code=409,
            detail="No available Google OAuth app. All configured apps reached the mailbox limit.",
        )

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(
            status_code=400,
            detail="Selected Google OAuth app is missing client credentials.",
        )

    scope = oauth_app.scopes or (
        "https://www.googleapis.com/auth/gmail.modify "
        "https://www.googleapis.com/auth/userinfo.email"
    )

    state = encode_state(
        {
            "user_id": current_user.id,
            "oauth_app_id": oauth_app.id,
            "provider": "google",
        }
    )

    params = {
        "client_id": oauth_app.client_id,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "scope": scope,
        "state": state,
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return {"auth_url": url}


@router.get("/oauth/google/callback", response_model=MailboxOut)
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    state_data = decode_state(state)

    user_id = state_data.get("user_id")
    oauth_app_id = state_data.get("oauth_app_id")
    provider = state_data.get("provider")

    if not user_id or not oauth_app_id or provider != "google":
        raise HTTPException(status_code=400, detail="Invalid state payload")

    app_stmt = select(OAuthApp).where(
        OAuthApp.id == oauth_app_id,
        OAuthApp.user_id == user_id,
        OAuthApp.provider == "google",
        OAuthApp.is_active.is_(True),
    )
    app_res = await db.execute(app_stmt)
    oauth_app = app_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(status_code=404, detail="OAuth app not found or inactive")

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(
            status_code=400,
            detail="Selected Google OAuth app is missing client credentials.",
        )

    count_stmt = select(func.count(Mailbox.id)).where(
        Mailbox.oauth_app_id == oauth_app.id
    )
    count_res = await db.execute(count_stmt)
    mailbox_count = count_res.scalar() or 0

    async with httpx.AsyncClient(timeout=30) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": oauth_app.client_id,
                "client_secret": oauth_app.client_secret,
                "code": code,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code: {token_res.text}",
        )

    token_data = token_res.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    expiry = datetime.utcnow() + timedelta(seconds=expires_in or 3600)

    async with httpx.AsyncClient(timeout=30) as client:
        me_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if me_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch user info: {me_res.text}",
        )

    me_data = me_res.json()
    email = me_data["email"]
    name = me_data.get("name")
    normalized_scope = " ".join(token_data.get("scope", "").split())

    stmt = select(Mailbox).where(
        Mailbox.user_id == user_id,
        Mailbox.provider == "google",
        Mailbox.email == email,
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.oauth_app_id = oauth_app.id
        existing.access_token = access_token
        existing.refresh_token = refresh_token or existing.refresh_token
        existing.token_expiry = expiry
        existing.scope = normalized_scope
        existing.display_name = name or existing.display_name
        existing.warmup_enabled = True
        mailbox = existing
    else:
        if mailbox_count >= GOOGLE_APP_MAX_MAILBOXES:
            raise HTTPException(
                status_code=409,
                detail="Selected Google OAuth app reached the mailbox limit.",
            )

        mailbox = Mailbox(
            user_id=user_id,
            oauth_app_id=oauth_app.id,
            provider="google",
            email=email,
            display_name=name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            scope=normalized_scope,
            warmup_enabled=True,
        )
        db.add(mailbox)

    await db.commit()
    await db.refresh(mailbox)
    return mailbox




@router.delete("/{mailbox_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mailbox(
    mailbox_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Mailbox).where(
        Mailbox.id == mailbox_id,
        Mailbox.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    mailbox = res.scalar_one_or_none()

    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    if mailbox.provider == "google":
        try:
            await revoke_google_mailbox_access(mailbox)
        except HTTPException:
            pass

    await db.delete(mailbox)
    await db.commit()
    return