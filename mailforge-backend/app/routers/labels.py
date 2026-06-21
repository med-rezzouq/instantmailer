from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.label import Label
from app.models.user import User
from app.schemas.label import LabelCreate, LabelUpdate, LabelOut

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("", response_model=List[LabelOut])
async def list_labels(
    q: Optional[str] = Query(
        default=None,
        description="Optional label name search",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of labels to return",
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of labels to skip",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Label).where(Label.user_id == current_user.id)

    if q and q.strip():
        term = q.strip()
        stmt = stmt.where(Label.name.ilike(f"%{term}%"))

    stmt = stmt.order_by(Label.name.asc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/search", response_model=List[LabelOut])
async def search_labels(
    q: str = Query(
        ...,
        min_length=1,
        description="Search labels by name",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of search results",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    term = q.strip()
    if not term:
        return []

    stmt = (
        select(Label)
        .where(
            Label.user_id == current_user.id,
            Label.name.ilike(f"%{term}%"),
        )
        .order_by(
            case(
                (func.lower(Label.name) == term.lower(), 0),
                (func.lower(Label.name).like(f"{term.lower()}%"), 1),
                else_=2,
            ),
            Label.name.asc(),
        )
        .limit(limit)
    )

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{label_id}", response_model=LabelOut)
async def get_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Label).where(
        Label.id == label_id,
        Label.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    label = res.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    return label


@router.post("", response_model=LabelOut, status_code=status.HTTP_201_CREATED)
async def create_label(
    payload: LabelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Label name is required")

    stmt = select(Label).where(
        Label.user_id == current_user.id,
        func.lower(Label.name) == name.lower(),
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Label already exists")

    label = Label(
        user_id=current_user.id,
        name=name,
        description=payload.description.strip() if payload.description else None,
    )
    db.add(label)
    await db.commit()
    await db.refresh(label)
    return label


@router.put("/{label_id}", response_model=LabelOut)
async def update_label(
    label_id: int,
    payload: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Label).where(
        Label.id == label_id,
        Label.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    label = res.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Label name is required")

        existing_stmt = select(Label).where(
            Label.user_id == current_user.id,
            func.lower(Label.name) == name.lower(),
            Label.id != label_id,
        )
        existing_res = await db.execute(existing_stmt)
        existing = existing_res.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="Label already exists")

        label.name = name

    if payload.description is not None:
        label.description = payload.description.strip() or None

    await db.commit()
    await db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Label).where(
        Label.id == label_id,
        Label.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    label = res.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    await db.delete(label)
    await db.commit()
    return