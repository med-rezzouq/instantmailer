from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.oauth_apps import OAuthApp
from app.schemas.oauth_apps import OAuthAppCreate, OAuthAppUpdate, OAuthAppOut

router = APIRouter(prefix="/oauthapps", tags=["oauthapps"])


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def to_oauth_app_out(app: OAuthApp) -> OAuthAppOut:
    return OAuthAppOut(
        id=app.id,
        user_id=app.user_id,
        provider=app.provider,
        name=app.name,
        client_id=app.client_id,
        client_secret_masked=mask_secret(app.client_secret),
        redirect_uri=app.redirect_uri,
        scopes=app.scopes,
        is_active=app.is_active,
        owner_email=app.owner_email,
        project_id=app.project_id,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


@router.get("", response_model=List[OAuthAppOut])
async def list_oauth_apps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(OAuthApp)
        .where(OAuthApp.user_id == current_user.id)
        .order_by(OAuthApp.created_at.desc(), OAuthApp.id.desc())
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    return [to_oauth_app_out(item) for item in items]


@router.get("/{app_id}", response_model=OAuthAppOut)
async def get_oauth_app(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(OAuthApp).where(
        OAuthApp.id == app_id,
        OAuthApp.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="OAuth app not found")

    return to_oauth_app_out(app)


@router.post("", response_model=OAuthAppOut, status_code=status.HTTP_201_CREATED)
async def create_oauth_app(
    payload: OAuthAppCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = OAuthApp(
        user_id=current_user.id,
        provider=payload.provider,
        name=payload.name,
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        redirect_uri=payload.redirect_uri,
        scopes=payload.scopes,
        is_active=payload.is_active,
        owner_email=payload.owner_email,
        project_id=payload.project_id,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return to_oauth_app_out(app)


@router.put("/{app_id}", response_model=OAuthAppOut)
async def update_oauth_app(
    app_id: int,
    payload: OAuthAppUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(OAuthApp).where(
        OAuthApp.id == app_id,
        OAuthApp.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="OAuth app not found")

    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(app, field, value)

    await db.commit()
    await db.refresh(app)
    return to_oauth_app_out(app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_oauth_app(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(OAuthApp).where(
        OAuthApp.id == app_id,
        OAuthApp.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="OAuth app not found")

    await db.delete(app)
    await db.commit()
    return None