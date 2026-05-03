from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.campaign_event import CampaignEvent, EventType

router = APIRouter(prefix="/track", tags=["Tracking"])

PIXEL = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

@router.get("/open/{token}")
async def track_open(token: str, db: AsyncSession = Depends(get_db)):
    try:
        parts = token.split("-")
        campaign_id, contact_id, step_id = int(parts[0]), int(parts[1]), int(parts[2])
        event = CampaignEvent(
            campaign_id=campaign_id, contact_id=contact_id,
            step_id=step_id, event_type=EventType.open,
            occurred_at=datetime.utcnow()
        )
        db.add(event)
        await db.commit()
    except Exception:
        pass
    return Response(content=PIXEL, media_type="image/gif")


@router.get("/click/{campaign_id}/{contact_id}/{step_id}")
async def track_click(
    campaign_id: int, contact_id: int, step_id: int,
    url: str = "",
    db: AsyncSession = Depends(get_db)
):
    try:
        event = CampaignEvent(
            campaign_id=campaign_id, contact_id=contact_id,
            step_id=step_id, event_type=EventType.click,
            occurred_at=datetime.utcnow(),
            metadata_={"url": url}
        )
        db.add(event)
        await db.commit()
    except Exception:
        pass
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=url or "/")