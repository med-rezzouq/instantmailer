from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.powermta_reply import PowerMTAReply
from app.models.campaign_contact import CampaignContact, ContactStatus
from app.models.campaign_event import CampaignEvent, EventType

router = APIRouter(prefix="/internal/powermta", tags=["PowerMTA"])

@router.post("/reply")
async def receive_reply(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Called by PowerMTA pipe script when a reply arrives.
    Expects JSON: { to, from, subject, body, headers }
    """
    data = await request.json()
    to_address = data.get("to", "")

    # Parse reply+{campaign_id}+{contact_id}+{step_id}@domain
    campaign_id = contact_id = step_id = None
    try:
        local = to_address.split("@")[0]
        parts = local.split("+")
        if len(parts) >= 4:
            campaign_id = int(parts[1])
            contact_id  = int(parts[2])
            step_id     = int(parts[3])
    except Exception:
        pass

    # Save raw reply
    reply = PowerMTAReply(
        campaign_id=campaign_id, contact_id=contact_id, step_id=step_id,
        from_email=data.get("from", ""),
        to_address=to_address,
        subject=data.get("subject", ""),
        body_text=data.get("body", ""),
        raw_headers=str(data.get("headers", "")),
    )
    db.add(reply)

    # Mark contact as replied
    if campaign_id and contact_id:
        result = await db.execute(
            select(CampaignContact).where(
                CampaignContact.campaign_id == campaign_id,
                CampaignContact.contact_id == contact_id
            )
        )
        cc = result.scalar_one_or_none()
        if cc:
            cc.status = ContactStatus.replied
            cc.replied_at = datetime.utcnow()
            cc.their_last_reply_at = datetime.utcnow()
            cc.in_reply_thread = True

        # Record reply event
        event = CampaignEvent(
            campaign_id=campaign_id, contact_id=contact_id,
            step_id=step_id, event_type=EventType.reply,
            occurred_at=datetime.utcnow()
        )
        db.add(event)

    reply.processed = True
    await db.commit()
    return {"ok": True}