from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.campaign import Campaign
from app.models.analytics import EmailEvent
from app.models.contact import Contact
from app.schemas.analytics import CampaignStats, DashboardStats
from app.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_campaigns = (await db.execute(
        select(func.count()).where(Campaign.user_id == current_user.id)
    )).scalar()
    total_contacts = (await db.execute(
        select(func.count()).where(Contact.user_id == current_user.id)
    )).scalar()

    sent_result = await db.execute(
        select(func.count(EmailEvent.id)).join(Campaign).where(
            Campaign.user_id == current_user.id, EmailEvent.event_type == "sent"
        )
    )
    total_sent = sent_result.scalar() or 0

    opened_count = (await db.execute(
        select(func.count(EmailEvent.id)).join(Campaign).where(
            Campaign.user_id == current_user.id, EmailEvent.event_type == "opened"
        )
    )).scalar() or 0

    clicked_count = (await db.execute(
        select(func.count(EmailEvent.id)).join(Campaign).where(
            Campaign.user_id == current_user.id, EmailEvent.event_type == "clicked"
        )
    )).scalar() or 0

    avg_open_rate  = round((opened_count  / total_sent * 100), 2) if total_sent else 0.0
    avg_click_rate = round((clicked_count / total_sent * 100), 2) if total_sent else 0.0

    return DashboardStats(
        total_campaigns=total_campaigns,
        total_contacts=total_contacts,
        total_emails_sent=total_sent,
        avg_open_rate=avg_open_rate,
        avg_click_rate=avg_click_rate,
    )

@router.get("/campaigns/{campaign_id}", response_model=CampaignStats)
async def campaign_stats(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    def count_event(event_type: str):
        return select(func.count(EmailEvent.id)).where(
            EmailEvent.campaign_id == campaign_id,
            EmailEvent.event_type == event_type,
        )

    sent     = (await db.execute(count_event("sent"))).scalar() or 0
    opened   = (await db.execute(count_event("opened"))).scalar() or 0
    clicked  = (await db.execute(count_event("clicked"))).scalar() or 0
    bounced  = (await db.execute(count_event("bounced"))).scalar() or 0

    return CampaignStats(
        campaign_id=campaign_id,
        campaign_name=campaign.name,
        total_sent=sent,
        total_opened=opened,
        total_clicked=clicked,
        total_bounced=bounced,
        open_rate=round(opened / sent * 100, 2) if sent else 0,
        click_rate=round(clicked / sent * 100, 2) if sent else 0,
        bounce_rate=round(bounced / sent * 100, 2) if sent else 0,
    )
