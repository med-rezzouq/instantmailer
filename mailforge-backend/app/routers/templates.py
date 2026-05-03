from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.template import EmailTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateOut
from app.dependencies import get_current_user

router = APIRouter(prefix="/templates", tags=["Templates"])

@router.get("", response_model=List[TemplateOut])
async def list_templates(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.user_id == current_user.id))
    return result.scalars().all()

@router.post("", response_model=TemplateOut, status_code=201)
async def create_template(
    payload: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tmpl = EmailTemplate(user_id=current_user.id, **payload.model_dump())
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl

@router.get("/{template_id}")
async def get_template(template_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl

@router.put("/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: int, payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl

@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(tmpl)
    await db.commit()