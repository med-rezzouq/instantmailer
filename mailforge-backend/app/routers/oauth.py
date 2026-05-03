import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.oauth_token import OAuthToken, OAuthProvider
from app.services import microsoft_service, google_service
from app.dependencies import get_current_user
from app.config import get_settings

router   = APIRouter(prefix="/oauth", tags=["OAuth"])
settings = get_settings()

# ── Microsoft ──────────────────────────────────────────────────────────────
@router.get("/microsoft/connect")
async def microsoft_connect(current_user: User = Depends(get_current_user)):
    state = f"{current_user.id}:{secrets.token_urlsafe(16)}"
    url   = microsoft_service.get_auth_url(state)
    return {"auth_url": url}

@router.get("/microsoft/callback")
async def microsoft_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    user_id = int(state.split(":")[0])
    tokens  = await microsoft_service.exchange_code(code)
    expiry  = None
    if "expires_in" in tokens:
        from datetime import timedelta
        expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])

    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == OAuthProvider.MICROSOFT)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.access_token  = tokens["access_token"]
        existing.refresh_token = tokens.get("refresh_token", existing.refresh_token)
        existing.token_expiry  = expiry
    else:
        db.add(OAuthToken(
            user_id=user_id, provider=OAuthProvider.MICROSOFT,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_expiry=expiry,
        ))
    await db.commit()
    return RedirectResponse(url=f"{settings.FRONTEND_URL}?oauth=microsoft&status=success")

# ── Google ────────────────────────────────────────────────────────────────
@router.get("/google/connect")
async def google_connect(current_user: User = Depends(get_current_user)):
    state = f"{current_user.id}:{secrets.token_urlsafe(16)}"
    url   = google_service.get_auth_url(state)
    return {"auth_url": url}

@router.get("/google/callback")
async def google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    user_id = int(state.split(":")[0])
    tokens  = await google_service.exchange_code(code)
    expiry  = None
    if "expires_in" in tokens:
        from datetime import timedelta
        expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])

    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == OAuthProvider.GOOGLE)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.access_token  = tokens["access_token"]
        existing.refresh_token = tokens.get("refresh_token", existing.refresh_token)
        existing.token_expiry  = expiry
    else:
        db.add(OAuthToken(
            user_id=user_id, provider=OAuthProvider.GOOGLE,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_expiry=expiry,
        ))
    await db.commit()
    return RedirectResponse(url=f"{settings.FRONTEND_URL}?oauth=google&status=success")

@router.get("/status")
async def oauth_status(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == current_user.id))
    tokens = result.scalars().all()
    return {p.provider.value: True for p in tokens}
