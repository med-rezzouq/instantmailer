from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, TokenRefresh, UserOut
from app.services.auth_service import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    sub = str(user.id)
    return TokenResponse(
        access_token=create_access_token({"sub": sub}),
        refresh_token=create_refresh_token({"sub": sub}),
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    sub = str(user.id)
    return TokenResponse(
        access_token=create_access_token({"sub": sub}),
        refresh_token=create_refresh_token({"sub": sub}),
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: TokenRefresh):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    sub = data["sub"]
    return TokenResponse(
        access_token=create_access_token({"sub": sub}),
        refresh_token=create_refresh_token({"sub": sub}),
    )

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
