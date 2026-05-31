from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.warmup_task import WarmupTask
from app.schemas.warmup import (
    WarmupTaskCreate,
    WarmupTaskUpdate,
    WarmupTaskOut,
)

router = APIRouter(prefix="/warmup-tasks", tags=["warmup"])


@router.get("", response_model=List[WarmupTaskOut])
async def list_warmup_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(WarmupTask).where(WarmupTask.user_id == current_user.id)
    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return tasks


@router.post("", response_model=WarmupTaskOut, status_code=status.HTTP_201_CREATED)
async def create_warmup_task(
    task_in: WarmupTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = WarmupTask(
        user_id=current_user.id,
        **task_in.model_dump(),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/{task_id}", response_model=WarmupTaskOut)
async def update_warmup_task(
    task_id: int,
    task_in: WarmupTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    data = task_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warmup_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    await db.delete(task)
    await db.commit()
    return