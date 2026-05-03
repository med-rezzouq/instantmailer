from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_step import CampaignStep, StepType, DelayFrom
from app.models.campaign_sender import CampaignSender, SenderType
from app.models.campaign_contact import CampaignContact, ContactStatus
from app.models.campaign_event import CampaignEvent, EventType
from app.models.campaign_run import CampaignRun, RunStatus
from app.models.contact import Contact
from app.models.smtp_config import SMTPConfig

router = APIRouter(prefix="/v2/campaigns", tags=["Campaigns V2"])


# ── Schemas ───────────────────────────────────────────────────

class StepSchema(BaseModel):
    step_number: int
    step_type: StepType = StepType.initial
    name: Optional[str] = None
    subject: str
    html_body: Optional[str] = None
    plain_body: Optional[str] = None
    delay_days: int = 0
    delay_hours: int = 0
    delay_from: DelayFrom = DelayFrom.most_recent

class SenderSchema(BaseModel):
    sender_type: SenderType
    sender_id: int
    sender_label: Optional[str] = None
    quota: int

class CampaignCreateSchema(BaseModel):
    name: str
    segment_tags: List[str] = []
    track_opens: bool = True
    track_clicks: bool = True
    steps: List[StepSchema]
    senders: List[SenderSchema]

class CampaignOut(BaseModel):
    id: int
    name: str
    status: str
    total_contacts: int
    new_contacts_since_send: int
    created_at: datetime
    sent_at: Optional[datetime]
    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────

@router.get("", response_model=List[CampaignOut])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Campaign).where(Campaign.user_id == current_user.id).order_by(Campaign.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate sender quotas
    total_quota = sum(s.quota for s in data.senders)

    # Count contacts
    contact_count_result = await db.execute(
        select(func.count(Contact.id)).where(Contact.user_id == current_user.id, Contact.is_subscribed == True)
    )
    total_contacts = contact_count_result.scalar()

    if total_quota > total_contacts:
        raise HTTPException(status_code=400, detail=f"Total sender quota ({total_quota}) exceeds available contacts ({total_contacts})")

    campaign = Campaign(
        user_id=current_user.id,
        name=data.name,
        segment_tags=data.segment_tags,
        track_opens=data.track_opens,
        track_clicks=data.track_clicks,
        total_contacts=total_contacts,
    )
    db.add(campaign)
    await db.flush()

    # Add steps
    for s in data.steps:
        step = CampaignStep(campaign_id=campaign.id, **s.model_dump())
        db.add(step)

    # Add senders
    for s in data.senders:
        sender = CampaignSender(campaign_id=campaign.id, **s.model_dump())
        db.add(sender)

    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Load steps
    steps_result = await db.execute(select(CampaignStep).where(CampaignStep.campaign_id == campaign_id))
    steps = steps_result.scalars().all()

    # Load senders
    senders_result = await db.execute(select(CampaignSender).where(CampaignSender.campaign_id == campaign_id))
    senders = senders_result.scalars().all()

    # Load stats per step
    stats = {}
    for et in EventType:
        r = await db.execute(
            select(CampaignEvent.step_id, func.count(CampaignEvent.id))
            .where(CampaignEvent.campaign_id == campaign_id, CampaignEvent.event_type == et)
            .group_by(CampaignEvent.step_id)
        )
        for step_id, count in r.all():
            if step_id not in stats:
                stats[step_id] = {}
            stats[step_id][et.value] = count

    # Load runs
    runs_result = await db.execute(
        select(CampaignRun).where(CampaignRun.campaign_id == campaign_id).order_by(CampaignRun.started_at.desc())
    )
    runs = runs_result.scalars().all()

    return {
        "id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "total_contacts": campaign.total_contacts,
        "new_contacts_since_send": campaign.new_contacts_since_send,
        "track_opens": campaign.track_opens,
        "track_clicks": campaign.track_clicks,
        "created_at": campaign.created_at,
        "sent_at": campaign.sent_at,
        "steps": [
            {
                "id": s.id, "step_number": s.step_number, "step_type": s.step_type,
                "name": s.name, "subject": s.subject,
                "delay_days": s.delay_days, "delay_hours": s.delay_hours,
                "delay_from": s.delay_from,
                "stats": stats.get(s.id, {})
            } for s in steps
        ],
        "senders": [
            {"id": s.id, "sender_type": s.sender_type, "sender_id": s.sender_id,
             "sender_label": s.sender_label, "quota": s.quota, "sent_count": s.sent_count}
            for s in senders
        ],
        "runs": [
            {"id": r.id, "status": r.status, "total_sent": r.total_sent,
             "total_failed": r.total_failed, "started_at": r.started_at, "completed_at": r.completed_at}
            for r in runs
        ]
    }


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.running
    campaign.sent_at = datetime.utcnow()
    await db.commit()

    background_tasks.add_task(run_campaign_send, campaign_id)
    return {"message": "Campaign send started", "campaign_id": campaign_id}


@router.get("/{campaign_id}/contacts")
async def get_campaign_contacts(
    campaign_id: int,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(CampaignContact, Contact).join(
        Contact, CampaignContact.contact_id == Contact.id
    ).where(CampaignContact.campaign_id == campaign_id)

    if status_filter:
        query = query.where(CampaignContact.status == status_filter)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": cc.id, "status": cc.status,
            "in_reply_thread": cc.in_reply_thread,
            "last_sent_at": cc.last_sent_at,
            "replied_at": cc.replied_at,
            "email": c.email,
            "name": f"{c.first_name or ''} {c.last_name or ''}".strip()
        }
        for cc, c in rows
    ]


@router.get("/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stats = {}
    for et in EventType:
        r = await db.execute(
            select(func.count(CampaignEvent.id))
            .where(CampaignEvent.campaign_id == campaign_id, CampaignEvent.event_type == et)
        )
        stats[et.value] = r.scalar() or 0

    # Per-step breakdown
    steps_result = await db.execute(select(CampaignStep).where(CampaignStep.campaign_id == campaign_id))
    steps = steps_result.scalars().all()

    step_stats = []
    for step in steps:
        s = {"step_id": step.id, "step_name": step.name, "step_number": step.step_number, "step_type": step.step_type}
        for et in EventType:
            r = await db.execute(
                select(func.count(CampaignEvent.id))
                .where(CampaignEvent.campaign_id == campaign_id, CampaignEvent.step_id == step.id, CampaignEvent.event_type == et)
            )
            s[et.value] = r.scalar() or 0
        step_stats.append(s)

    return {"totals": stats, "per_step": step_stats}


# ── Background send task ──────────────────────────────────────

async def run_campaign_send(campaign_id: int):
    """
    Distributes emails across senders according to their quota.
    Each sender gets a slice of contacts up to their quota.
    """
    from app.database import AsyncSessionLocal
    from app.services.send_engine import send_via_smtp, build_reply_to, render_template
    import uuid

    async with AsyncSessionLocal() as db:
        try:
            # Load campaign
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalar_one_or_none()
            if not campaign:
                return

            # Load initial step
            step_result = await db.execute(
                select(CampaignStep).where(
                    CampaignStep.campaign_id == campaign_id,
                    CampaignStep.step_type == StepType.initial
                )
            )
            step = step_result.scalar_one_or_none()
            if not step:
                return

            # Load senders
            senders_result = await db.execute(select(CampaignSender).where(CampaignSender.campaign_id == campaign_id))
            senders = senders_result.scalars().all()

            # Load contacts
            contacts_result = await db.execute(
                select(Contact).where(Contact.user_id == campaign.user_id, Contact.is_subscribed == True)
            )
            contacts = contacts_result.scalars().all()

            # Create run record
            run = CampaignRun(campaign_id=campaign_id, step_id=step.id, status=RunStatus.running)
            db.add(run)
            await db.flush()

            # Distribute contacts across senders by quota
            contact_index = 0
            total_sent = 0
            total_failed = 0

            for sender in senders:
                if contact_index >= len(contacts):
                    break

                # Load smtp config
                smtp_result = await db.execute(select(SMTPConfig).where(SMTPConfig.id == sender.sender_id))
                smtp = smtp_result.scalar_one_or_none()
                if not smtp:
                    continue

                sender_contacts = contacts[contact_index: contact_index + sender.quota]
                contact_index += sender.quota

                for contact in sender_contacts:
                    html = render_template(step.html_body or "", {
                        "first_name": contact.first_name,
                        "last_name": contact.last_name,
                        "email": contact.email,
                        "name": f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                    })
                    msg_id = str(uuid.uuid4())
                    reply_to = build_reply_to(campaign_id, contact.id, step.id)

                    success = await send_via_smtp(
                        smtp_config=smtp,
                        to_email=contact.email,
                        subject=step.subject,
                        html_body=html,
                        plain_body=step.plain_body or "",
                        reply_to=reply_to,
                        message_id=msg_id,
                        campaign_id=campaign_id,
                        contact_id=contact.id,
                        step_id=step.id
                    )

                    if success:
                        total_sent += 1
                        sender.sent_count += 1
                        # Record campaign contact
                        cc = CampaignContact(
                            campaign_id=campaign_id,
                            contact_id=contact.id,
                            current_step_id=step.id,
                            last_sent_at=datetime.utcnow(),
                            our_last_sent_at=datetime.utcnow()
                        )
                        db.add(cc)
                        # Record sent event
                        event = CampaignEvent(
                            campaign_id=campaign_id,
                            step_id=step.id,
                            contact_id=contact.id,
                            event_type=EventType.sent
                        )
                        db.add(event)
                    else:
                        total_failed += 1

            run.status = RunStatus.completed
            run.total_sent = total_sent
            run.total_failed = total_failed
            run.completed_at = datetime.utcnow()
            campaign.status = CampaignStatus.completed

            await db.commit()

        except Exception as e:
            print(f"Campaign send error: {e}")