"""
Delivery status webhooks — called by Microsoft/Google or your own tracking pixel.
These endpoints are PUBLIC (no JWT auth) but should be protected with a shared secret
in production (pass as a query param ?secret=... and verify against env var).
"""
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.database import get_db
from app.models.analytics import EmailEvent
from app.models.contact import Contact
from app.models.campaign import CampaignRecipient

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/delivery")
async def delivery_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Generic delivery status webhook.
    Payload: { campaign_id, contact_email, event_type, metadata }
    event_type: opened | clicked | bounced | unsubscribed
    """
    body = await request.json()
    campaign_id  = body.get("campaign_id")
    contact_email = body.get("contact_email")
    event_type   = body.get("event_type")
    metadata     = body.get("metadata", {})
    ip_address   = request.client.host if request.client else None
    user_agent   = request.headers.get("user-agent", "")

    if not all([campaign_id, contact_email, event_type]):
        raise HTTPException(status_code=422, detail="Missing required fields")

    result = await db.execute(select(Contact).where(Contact.email == contact_email))
    contact = result.scalar_one_or_none()

    event = EmailEvent(
        campaign_id=campaign_id,
        contact_id=contact.id if contact else None,
        event_type=event_type,
        event_metadata=json.dumps(metadata),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)

    if contact:
        if event_type == "opened":
            contact.open_count += 1
        elif event_type == "clicked":
            contact.click_count += 1
        elif event_type == "unsubscribed":
            contact.is_subscribed = False

    await db.commit()
    return {"status": "recorded", "event": event_type}

@router.get("/track/open/{campaign_id}/{contact_id}")
async def track_open(campaign_id: int, contact_id: int, db: AsyncSession = Depends(get_db), request: Request = None):
    """1x1 tracking pixel endpoint — embed in HTML email as <img> src."""
    event = EmailEvent(
        campaign_id=campaign_id,
        contact_id=contact_id,
        event_type="opened",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent", "") if request else "",
    )
    db.add(event)
    contact = await db.get(Contact, contact_id)
    if contact:
        contact.open_count += 1
    await db.commit()
    # Return 1x1 transparent GIF
    from fastapi.responses import Response
    gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return Response(content=gif, media_type="image/gif")
