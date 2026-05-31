from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode
import os
import httpx

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.mailbox import Mailbox  # you need to create this model
from app.schemas.mailbox import MailboxOut  # you need to create this schema

# TODO: move these into your config.py / env vars

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

router = APIRouter(prefix="/mailboxes", tags=["mailboxes"])


@router.get("", response_model=List[MailboxOut])
async def list_mailboxes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all connected mailboxes for the current user.
    """
    stmt = select(Mailbox).where(Mailbox.user_id == current_user.id)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/connect/google")
async def connect_google(
    current_user: User = Depends(get_current_user),
):
    """
    Start OAuth flow for Gmail.
    Returns an auth_url that the frontend should redirect the user to.
    """
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "scope": "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/userinfo.email",
        "state": str(current_user.id),
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return {"auth_url": url}


@router.get("/oauth/google/callback", response_model=MailboxOut)
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth callback endpoint for Gmail.
    Google will redirect the user here with ?code=...&state=...
    This exchanges the code for tokens, fetches the email, and stores a Mailbox.
    """
    # state is the user_id you set in connect_google
    try:
        user_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
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

    # Fetch email address for this access token
    async with httpx.AsyncClient() as client:
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

    # Upsert: if mailbox for this user+email+provider exists, update it
    stmt = select(Mailbox).where(
        Mailbox.user_id == user_id,
        Mailbox.provider == "google",
        Mailbox.email == email,
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.token_expiry = expiry
        existing.scope = " ".join(token_data.get("scope", "").split())
        existing.display_name = name or existing.display_name
        existing.warmup_enabled = True
        mailbox = existing
    else:
        mailbox = Mailbox(
            user_id=user_id,
            provider="google",
            email=email,
            display_name=name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            scope=" ".join(token_data.get("scope", "").split()),
            warmup_enabled=True,
        )
        db.add(mailbox)

    await db.commit()
    await db.refresh(mailbox)
    return mailbox