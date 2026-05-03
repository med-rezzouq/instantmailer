from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import smtplib, ssl

from app.database import get_db
from app.models.smtp_config import SMTPConfig
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/smtp", tags=["SMTP"])

class SMTPConfigCreate(BaseModel):
    name: str
    host: str
    port: int = 587
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None

class SMTPConfigUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    is_active: Optional[bool] = None

class SMTPConfigOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: str
    use_tls: bool
    use_ssl: bool
    from_email: Optional[str]
    from_name: Optional[str]
    is_active: bool
    class Config:
        from_attributes = True

@router.get("", response_model=List[SMTPConfigOut])
async def list_smtp(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SMTPConfig).where(SMTPConfig.user_id == current_user.id))
    return result.scalars().all()

@router.post("", response_model=SMTPConfigOut, status_code=status.HTTP_201_CREATED)
async def create_smtp(data: SMTPConfigCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = SMTPConfig(**data.model_dump(), user_id=current_user.id)
    db.add(config); await db.commit(); await db.refresh(config)
    return config

@router.get("/{config_id}", response_model=SMTPConfigOut)
async def get_smtp(config_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SMTPConfig).where(SMTPConfig.id == config_id, SMTPConfig.user_id == current_user.id))
    config = result.scalar_one_or_none()
    if not config: raise HTTPException(status_code=404, detail="SMTP config not found")
    return config

@router.put("/{config_id}", response_model=SMTPConfigOut)
async def update_smtp(config_id: int, data: SMTPConfigUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SMTPConfig).where(SMTPConfig.id == config_id, SMTPConfig.user_id == current_user.id))
    config = result.scalar_one_or_none()
    if not config: raise HTTPException(status_code=404, detail="SMTP config not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(config, k, v)
    await db.commit(); await db.refresh(config)
    return config

@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_smtp(config_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SMTPConfig).where(SMTPConfig.id == config_id, SMTPConfig.user_id == current_user.id))
    config = result.scalar_one_or_none()
    if not config: raise HTTPException(status_code=404, detail="SMTP config not found")
    await db.delete(config); 