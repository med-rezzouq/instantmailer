from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlencode
import base64
import json
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.mailbox import Mailbox
from app.models.oauth_apps import OAuthApp
from app.models.warmup_task import WarmupTask
from app.schemas.mailbox import MailboxOut, MailboxImapCreate


GOOGLE_APP_MAX_MAILBOXES = int(os.getenv("GOOGLE_APP_MAX_MAILBOXES", "10"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "").rstrip("/")
FRONTEND_URL2 = os.getenv("FRONTEND_URL2", "").rstrip("/")

if not FRONTEND_URL:
    raise RuntimeError("FRONTEND_URL is not configured")

GOOGLE_REDIRECT_URI = f"{FRONTEND_URL}/mailboxes/oauth/google/callback"
MICROSOFT_REDIRECT_URI = f"{FRONTEND_URL}/mailboxes/oauth/microsoft/callback"
YAHOO_REDIRECT_URI = f"{FRONTEND_URL2}/mailboxes/oauth/yahoo/callback"

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


def mailbox_out_from_row(
    mailbox: Mailbox,
    oauth_app_name: str | None = None,
) -> MailboxOut:
    return MailboxOut(
        id=mailbox.id,
        user_id=mailbox.user_id,
        provider=mailbox.provider,
        access_protocol=mailbox.access_protocol,
        email=mailbox.email,
        display_name=mailbox.display_name,
        warmup_enabled=mailbox.warmup_enabled,
        last_sync_at=mailbox.last_sync_at,
        created_at=mailbox.created_at,
        updated_at=mailbox.updated_at,
        oauth_app_id=mailbox.oauth_app_id,
        oauth_app_name=oauth_app_name,
        imap_host=mailbox.imap_host,
        imap_port=mailbox.imap_port,
        imap_ssl=mailbox.imap_ssl,
        smtp_host=mailbox.smtp_host,
        smtp_port=mailbox.smtp_port,
        smtp_tls=mailbox.smtp_tls,
        username=mailbox.username,
        is_active=mailbox.is_active,
    )


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


async def get_task_with_oauth_app(
    db: AsyncSession,
    task_id: int,
    user_id: int,
) -> tuple[WarmupTask, OAuthApp]:
    task_stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == user_id,
    )
    task_res = await db.execute(task_stmt)
    task = task_res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    if not task.oauth_app_id:
        raise HTTPException(
            status_code=400,
            detail="Selected warmup task is not linked to any OAuth app",
        )

    oauth_stmt = select(OAuthApp).where(
        OAuthApp.id == task.oauth_app_id,
        OAuthApp.user_id == user_id,
        OAuthApp.is_active.is_(True),
    )
    oauth_res = await db.execute(oauth_stmt)
    oauth_app = oauth_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(
            status_code=404,
            detail="OAuth app linked to selected warmup task was not found",
        )

    return task, oauth_app


async def get_oauth_app_mailbox_limit(oauth_app: OAuthApp) -> int:
    return int(getattr(oauth_app, "mailboxes_per_oauth", None) or GOOGLE_APP_MAX_MAILBOXES)


async def get_oauth_app_mailbox_count(db: AsyncSession, oauth_app_id: int) -> int:
    count_stmt = select(func.count(Mailbox.id)).where(
        Mailbox.oauth_app_id == oauth_app_id
    )
    count_res = await db.execute(count_stmt)
    return count_res.scalar() or 0


async def ensure_oauth_app_has_capacity(
    db: AsyncSession,
    oauth_app: OAuthApp,
) -> None:
    limit = await get_oauth_app_mailbox_limit(oauth_app)
    count = await get_oauth_app_mailbox_count(db, oauth_app.id)

    if count >= limit:
        raise HTTPException(
            status_code=409,
            detail=f'OAuth app "{oauth_app.name}" reached the mailbox limit ({limit}).',
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
        mailbox_out_from_row(mailbox, oauth_app_name)
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
        mailbox_out_from_row(mailbox, oauth_app_name)
        for mailbox, oauth_app_name in rows
    ]


@router.get("/connect/google")
async def connect_google(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task, oauth_app = await get_task_with_oauth_app(db, task_id, current_user.id)

    if oauth_app.provider != "google":
        raise HTTPException(
            status_code=400,
            detail="Selected task is linked to a non-Google OAuth app",
        )

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(
            status_code=400,
            detail="Selected Google OAuth app is missing client credentials.",
        )

    await ensure_oauth_app_has_capacity(db, oauth_app)

    scope = oauth_app.scopes or (
        "https://www.googleapis.com/auth/gmail.modify "
        "https://www.googleapis.com/auth/userinfo.email"
    )

    state = encode_state(
        {
            "user_id": current_user.id,
            "task_id": task.id,
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
    task_id = state_data.get("task_id")
    oauth_app_id = state_data.get("oauth_app_id")
    provider = state_data.get("provider")

    if not user_id or not task_id or not oauth_app_id or provider != "google":
        raise HTTPException(status_code=400, detail="Invalid state payload")

    task_stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == user_id,
    )
    task_res = await db.execute(task_stmt)
    task = task_res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    if task.oauth_app_id != oauth_app_id:
        raise HTTPException(
            status_code=400,
            detail="Warmup task OAuth app does not match callback state",
        )

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
        existing.access_protocol = "oauth2"
        existing.access_token = access_token
        existing.refresh_token = refresh_token or existing.refresh_token
        existing.token_expiry = expiry
        existing.scope = normalized_scope
        existing.display_name = name or existing.display_name
        existing.warmup_enabled = True
        mailbox = existing
    else:
        if mailbox_count >= await get_oauth_app_mailbox_limit(oauth_app):
            raise HTTPException(
                status_code=409,
                detail="OAuth app reached the mailbox limit. Please add a new OAuth app or contact support.",
            )

        mailbox = Mailbox(
            user_id=user_id,
            oauth_app_id=oauth_app.id,
            provider="google",
            access_protocol="oauth2",
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

    oauth_name = getattr(oauth_app, "name", None)
    return mailbox_out_from_row(mailbox, oauth_name)


@router.get("/connect/microsoft")
async def connect_microsoft(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task, oauth_app = await get_task_with_oauth_app(db, task_id, current_user.id)

    if oauth_app.provider != "microsoft":
        raise HTTPException(
            status_code=400,
            detail="Selected task is linked to a non-Microsoft OAuth app",
        )

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(
            status_code=400,
            detail="Selected Microsoft OAuth app is missing client credentials.",
        )

    await ensure_oauth_app_has_capacity(db, oauth_app)

    scope = oauth_app.scopes or "offline_access User.Read Mail.Read Mail.ReadWrite Mail.Send"

    state = encode_state(
        {
            "user_id": current_user.id,
            "task_id": task.id,
            "oauth_app_id": oauth_app.id,
            "provider": "microsoft",
        }
    )

    tenant = getattr(oauth_app, "tenant_id", None) or "common"

    params = {
        "client_id": oauth_app.client_id,
        "redirect_uri": MICROSOFT_REDIRECT_URI,
        "response_type": "code",
        "response_mode": "query",
        "scope": scope,
        "state": state,
    }

    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?" + urlencode(params)
    return {"auth_url": url}


@router.get("/oauth/microsoft/callback", response_model=MailboxOut)
async def microsoft_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    state_data = decode_state(state)

    user_id = state_data.get("user_id")
    task_id = state_data.get("task_id")
    oauth_app_id = state_data.get("oauth_app_id")
    provider = state_data.get("provider")

    if not user_id or not task_id or not oauth_app_id or provider != "microsoft":
        raise HTTPException(status_code=400, detail="Invalid state payload")

    task_stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == user_id,
    )
    task_res = await db.execute(task_stmt)
    task = task_res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    if task.oauth_app_id != oauth_app_id:
        raise HTTPException(
            status_code=400,
            detail="Warmup task OAuth app does not match callback state",
        )

    app_stmt = select(OAuthApp).where(
        OAuthApp.id == oauth_app_id,
        OAuthApp.user_id == user_id,
        OAuthApp.provider == "microsoft",
        OAuthApp.is_active.is_(True),
    )
    app_res = await db.execute(app_stmt)
    oauth_app = app_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(status_code=404, detail="OAuth app not found or inactive")

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(
            status_code=400,
            detail="Selected Microsoft OAuth app is missing client credentials.",
        )

    tenant = getattr(oauth_app, "tenant_id", None) or "common"
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    async with httpx.AsyncClient(timeout=30) as client:
        token_res = await client.post(
            token_url,
            data={
                "client_id": oauth_app.client_id,
                "client_secret": oauth_app.client_secret,
                "code": code,
                "redirect_uri": MICROSOFT_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange Microsoft code: {token_res.text}",
        )

    token_data = token_res.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    expiry = datetime.utcnow() + timedelta(seconds=expires_in or 3600)
    normalized_scope = " ".join(token_data.get("scope", "").split())

    async with httpx.AsyncClient(timeout=30) as client:
        me_res = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if me_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch Microsoft user info: {me_res.text}",
        )

    me_data = me_res.json()
    email = (
        me_data.get("mail")
        or me_data.get("userPrincipalName")
        or me_data.get("preferred_username")
    )
    name = me_data.get("displayName")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Microsoft account email could not be resolved.",
        )

    stmt = select(Mailbox).where(
        Mailbox.user_id == user_id,
        Mailbox.provider == "microsoft",
        Mailbox.email == email,
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.oauth_app_id = oauth_app.id
        existing.provider = "microsoft"
        existing.access_protocol = "oauth2"
        existing.access_token = access_token
        existing.refresh_token = refresh_token or existing.refresh_token
        existing.token_expiry = expiry
        existing.scope = normalized_scope
        existing.display_name = name or existing.display_name
        existing.warmup_enabled = True
        existing.is_active = True
        mailbox = existing
    else:
        mailbox = Mailbox(
            user_id=user_id,
            oauth_app_id=oauth_app.id,
            provider="microsoft",
            access_protocol="oauth2",
            email=email,
            display_name=name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            scope=normalized_scope,
            warmup_enabled=True,
            is_active=True,
        )
        db.add(mailbox)

    await db.commit()
    await db.refresh(mailbox)

    oauth_name = getattr(oauth_app, "name", None)
    return mailbox_out_from_row(mailbox, oauth_name)


@router.post("/connect/imap", response_model=MailboxOut)
async def connect_imap(
    payload: MailboxImapCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Mailbox).where(
        Mailbox.user_id == current_user.id,
        Mailbox.email == payload.email,
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.provider = existing.provider or "custom"
        existing.access_protocol = "imap"
        existing.display_name = payload.display_name or existing.display_name
        existing.imap_host = payload.imap_host
        existing.imap_port = payload.imap_port
        existing.imap_ssl = payload.imap_ssl
        existing.smtp_host = payload.smtp_host
        existing.smtp_port = payload.smtp_port
        existing.smtp_tls = payload.smtp_tls
        existing.username = payload.username
        existing.password = payload.password
        existing.warmup_enabled = payload.warmup_enabled
        existing.is_active = payload.is_active
        mailbox = existing
    else:
        mailbox = Mailbox(
            user_id=current_user.id,
            oauth_app_id=None,
            provider="custom",
            access_protocol="imap",
            email=payload.email,
            display_name=payload.display_name,
            imap_host=payload.imap_host,
            imap_port=payload.imap_port,
            imap_ssl=payload.imap_ssl,
            smtp_host=payload.smtp_host,
            smtp_port=payload.smtp_port,
            smtp_tls=payload.smtp_tls,
            username=payload.username,
            password=payload.password,
            warmup_enabled=payload.warmup_enabled,
            is_active=payload.is_active,
        )
        db.add(mailbox)

    await db.commit()
    await db.refresh(mailbox)

    return mailbox_out_from_row(mailbox)


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


@router.get("/connect/yahoo")
async def connect_yahoo(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task, oauth_app = await get_task_with_oauth_app(db, task_id, current_user.id)

    if oauth_app.provider != "yahoo":
        raise HTTPException(
            status_code=400,
            detail="Selected task is linked to a non-Yahoo OAuth app",
        )

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(
            status_code=400,
            detail="Selected Yahoo OAuth app is missing client credentials.",
        )

    await ensure_oauth_app_has_capacity(db, oauth_app)

    scope = "openid"

    state = encode_state(
        {
            "user_id": current_user.id,
            "task_id": task.id,
            "oauth_app_id": oauth_app.id,
            "provider": "yahoo",
        }
    )

    params = {
        "client_id": oauth_app.client_id,
        "redirect_uri": YAHOO_REDIRECT_URI,
        "response_type": "code",
        "scope": scope,
        "state": state,
    }

    url = "https://api.login.yahoo.com/oauth2/request_auth?" + urlencode(params)
    return {"auth_url": url}


async def complete_yahoo_oauth(
    code: str,
    state: str,
    db: AsyncSession,
) -> MailboxOut:
    state_data = decode_state(state)

    user_id = state_data.get("user_id")
    task_id = state_data.get("task_id")
    oauth_app_id = state_data.get("oauth_app_id")
    provider = state_data.get("provider")

    if not user_id or not task_id or not oauth_app_id or provider != "yahoo":
        raise HTTPException(status_code=400, detail="Invalid state payload")

    task_stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == user_id,
    )
    task_res = await db.execute(task_stmt)
    task = task_res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    if task.oauth_app_id != oauth_app_id:
        raise HTTPException(
            status_code=400,
            detail="Warmup task OAuth app does not match callback state",
        )

    app_stmt = select(OAuthApp).where(
        OAuthApp.id == oauth_app_id,
        OAuthApp.user_id == user_id,
        OAuthApp.provider == "yahoo",
        OAuthApp.is_active.is_(True),
    )
    app_res = await db.execute(app_stmt)
    oauth_app = app_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(status_code=404, detail="OAuth app not found or inactive")

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(
            status_code=400,
            detail="Selected Yahoo OAuth app is missing client credentials.",
        )

    async with httpx.AsyncClient(timeout=30) as client:
        token_res = await client.post(
            "https://api.login.yahoo.com/oauth2/get_token",
            data={
                "client_id": oauth_app.client_id,
                "client_secret": oauth_app.client_secret,
                "code": code,
                "redirect_uri": YAHOO_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange Yahoo code: {token_res.text}",
        )

    token_data = token_res.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    expiry = datetime.utcnow() + timedelta(seconds=expires_in or 3600)
    normalized_scope = " ".join(token_data.get("scope", "").split())

    async with httpx.AsyncClient(timeout=30) as client:
        me_res = await client.get(
            "https://api.login.yahoo.com/openid/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if me_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch Yahoo user info: {me_res.text}",
        )

    me_data = me_res.json()
    email = me_data.get("email")
    name = me_data.get("name") or me_data.get("given_name")
    print("YAHOO USERINFO STATUS:", me_res.status_code)
    print("YAHOO USERINFO JSON:", me_res.text)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Yahoo account email could not be resolved.",
        )

    stmt = select(Mailbox).where(
        Mailbox.user_id == user_id,
        Mailbox.provider == "yahoo",
        Mailbox.email == email,
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.oauth_app_id = oauth_app.id
        existing.provider = "yahoo"
        existing.access_protocol = "oauth2"
        existing.access_token = access_token
        existing.refresh_token = refresh_token or existing.refresh_token
        existing.token_expiry = expiry
        existing.scope = normalized_scope
        existing.display_name = name or existing.display_name
        existing.warmup_enabled = True
        existing.is_active = True
        mailbox = existing
    else:
        await ensure_oauth_app_has_capacity(db, oauth_app)

        mailbox = Mailbox(
            user_id=user_id,
            oauth_app_id=oauth_app.id,
            provider="yahoo",
            access_protocol="oauth2",
            email=email,
            display_name=name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            scope=normalized_scope,
            warmup_enabled=True,
            is_active=True,
        )
        db.add(mailbox)

    await db.commit()
    await db.refresh(mailbox)

    oauth_name = getattr(oauth_app, "name", None)
    return mailbox_out_from_row(mailbox, oauth_name)


@router.get("/oauth/yahoo/callback", response_model=MailboxOut)
async def yahoo_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    return await complete_yahoo_oauth(code, state, db)


@router.post("/oauth/yahoo/callback", response_model=MailboxOut)
async def yahoo_callback_from_frontend(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    code = payload.get("code")
    state = payload.get("state")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    return await complete_yahoo_oauth(code, state, db)

# @router.get("/oauth/yahoo/callback", response_model=MailboxOut)
# async def yahoo_callback(
#     code: str,
#     state: str,
#     db: AsyncSession = Depends(get_db),
# ):
#     state_data = decode_state(state)

#     user_id = state_data.get("user_id")
#     task_id = state_data.get("task_id")
#     oauth_app_id = state_data.get("oauth_app_id")
#     provider = state_data.get("provider")

#     if not user_id or not task_id or not oauth_app_id or provider != "yahoo":
#         raise HTTPException(status_code=400, detail="Invalid state payload")

#     task_stmt = select(WarmupTask).where(
#         WarmupTask.id == task_id,
#         WarmupTask.user_id == user_id,
#     )
#     task_res = await db.execute(task_stmt)
#     task = task_res.scalar_one_or_none()

#     if not task:
#         raise HTTPException(status_code=404, detail="Warmup task not found")

#     if task.oauth_app_id != oauth_app_id:
#         raise HTTPException(
#             status_code=400,
#             detail="Warmup task OAuth app does not match callback state",
#         )

#     app_stmt = select(OAuthApp).where(
#         OAuthApp.id == oauth_app_id,
#         OAuthApp.user_id == user_id,
#         OAuthApp.provider == "yahoo",
#         OAuthApp.is_active.is_(True),
#     )
#     app_res = await db.execute(app_stmt)
#     oauth_app = app_res.scalar_one_or_none()

#     if not oauth_app:
#         raise HTTPException(status_code=404, detail="OAuth app not found or inactive")

#     if not oauth_app.client_id or not oauth_app.client_secret:
#         raise HTTPException(
#             status_code=400,
#             detail="Selected Yahoo OAuth app is missing client credentials.",
#         )

#     async with httpx.AsyncClient(timeout=30) as client:
#         token_res = await client.post(
#             "https://api.login.yahoo.com/oauth2/get_token",
#             data={
#                 "client_id": oauth_app.client_id,
#                 "client_secret": oauth_app.client_secret,
#                 "code": code,
#                 "redirect_uri": YAHOO_REDIRECT_URI,
#                 "grant_type": "authorization_code",
#             },
#             headers={"Content-Type": "application/x-www-form-urlencoded"},
#         )

#     if token_res.status_code != 200:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Failed to exchange Yahoo code: {token_res.text}",
#         )

#     token_data = token_res.json()
#     access_token = token_data["access_token"]
#     refresh_token = token_data.get("refresh_token")
#     expires_in = token_data.get("expires_in")
#     expiry = datetime.utcnow() + timedelta(seconds=expires_in or 3600)
#     normalized_scope = " ".join(token_data.get("scope", "").split())

#     async with httpx.AsyncClient(timeout=30) as client:
#         me_res = await client.get(
#             "https://api.login.yahoo.com/openid/v1/userinfo",
#             headers={"Authorization": f"Bearer {access_token}"},
#         )

#     if me_res.status_code != 200:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Failed to fetch Yahoo user info: {me_res.text}",
#         )

#     me_data = me_res.json()
#     email = me_data.get("email")
#     name = me_data.get("name") or me_data.get("given_name")

#     if not email:
#         raise HTTPException(
#             status_code=400,
#             detail="Yahoo account email could not be resolved.",
#         )

#     stmt = select(Mailbox).where(
#         Mailbox.user_id == user_id,
#         Mailbox.provider == "yahoo",
#         Mailbox.email == email,
#     )
#     res = await db.execute(stmt)
#     existing = res.scalar_one_or_none()

#     if existing:
#         existing.oauth_app_id = oauth_app.id
#         existing.provider = "yahoo"
#         existing.access_protocol = "oauth2"
#         existing.access_token = access_token
#         existing.refresh_token = refresh_token or existing.refresh_token
#         existing.token_expiry = expiry
#         existing.scope = normalized_scope
#         existing.display_name = name or existing.display_name
#         existing.warmup_enabled = True
#         existing.is_active = True
#         mailbox = existing
#     else:
#         mailbox = Mailbox(
#             user_id=user_id,
#             oauth_app_id=oauth_app.id,
#             provider="yahoo",
#             access_protocol="oauth2",
#             email=email,
#             display_name=name,
#             access_token=access_token,
#             refresh_token=refresh_token,
#             token_expiry=expiry,
#             scope=normalized_scope,
#             warmup_enabled=True,
#             is_active=True,
#         )
#         db.add(mailbox)

#     await db.commit()
#     await db.refresh(mailbox)

#     oauth_name = getattr(oauth_app, "name", None)
#     return mailbox_out_from_row(mailbox, oauth_name)