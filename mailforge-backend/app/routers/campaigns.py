from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.analytics import EmailEvent
from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_sender import CampaignSender, SenderType
from app.models.campaign_step import CampaignStep
from app.models.contact import Contact, ContactGroup, contact_tags
from app.models.smtp_config import SMTPConfig
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignOut,
    CampaignUpdate,
    InboundReplyIn,
)
from app.services.campaign_sequence_service import process_campaign_followups
from app.services.email_service import send_campaign

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


async def _validate_campaign_group(
    db: AsyncSession,
    user_id: int,
    group_id: int | None,
) -> None:
    if group_id is None:
        raise HTTPException(status_code=400, detail="Contact group is required")

    result = await db.execute(
        select(ContactGroup).where(
            ContactGroup.id == group_id,
            ContactGroup.user_id == user_id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=400, detail="Invalid contact group")


async def _sync_campaign_sender_from_provider(
    db: AsyncSession,
    campaign: Campaign,
    user_id: int,
) -> None:
    if campaign.provider_id is None:
        await db.execute(
            delete(CampaignSender).where(CampaignSender.campaign_id == campaign.id)
        )
        return

    result = await db.execute(
        select(SMTPConfig).where(
            SMTPConfig.id == campaign.provider_id,
            SMTPConfig.user_id == user_id,
        )
    )
    smtp = result.scalar_one_or_none()
    if not smtp:
        return

    result = await db.execute(
        select(CampaignSender).where(
            CampaignSender.campaign_id == campaign.id,
            CampaignSender.sender_type == SenderType.smtp,
            CampaignSender.sender_id == smtp.id,
        )
    )
    sender = result.scalar_one_or_none()

    if sender is None:
        sender = CampaignSender(
            campaign_id=campaign.id,
            sender_type=SenderType.smtp,
            sender_id=smtp.id,
            sender_label=f"{smtp.from_name} <{smtp.from_email}>",
            quota=campaign.total_contacts or 0,
            sent_count=0,
        )
        db.add(sender)
    else:
        sender.sender_label = f"{smtp.from_name} <{smtp.from_email}>"
        sender.quota = campaign.total_contacts or sender.quota

    await db.flush()


async def _campaign_to_out(db: AsyncSession, campaign: Campaign) -> CampaignOut:
    ordered_steps = sorted(campaign.steps or [], key=lambda x: x.step_number)

    initial_step = next(
        (
            step
            for step in ordered_steps
            if getattr(step.step_type, "value", step.step_type) == "initial"
        ),
        None,
    )

    followup_count = len(
        [
            step
            for step in ordered_steps
            if getattr(step.step_type, "value", step.step_type) != "initial"
        ]
    )

    return CampaignOut(
        id=campaign.id,
        user_id=campaign.user_id,
        name=campaign.name,
        status=campaign.status,
        preview_text=campaign.preview_text,
        from_name=campaign.from_name,
        reply_to=campaign.reply_to,
        group_id=campaign.group_id,
        provider_id=campaign.provider_id,
        segment_tags=campaign.segment_tags or [],
        track_opens=campaign.track_opens,
        track_clicks=campaign.track_clicks,
        is_followup=campaign.is_followup,
        parent_campaign_id=campaign.parent_campaign_id,
        max_bounces=campaign.max_bounces,
        max_complaints=campaign.max_complaints,
        max_unsubscribes=campaign.max_unsubscribes,
        max_followups=campaign.max_followups,
        stopped_by_condition=campaign.stopped_by_condition,
        stop_reason=campaign.stop_reason,
        total_contacts=campaign.total_contacts or 0,
        new_contacts_since_send=campaign.new_contacts_since_send or 0,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        sent_at=campaign.sent_at,
        scheduled_at=campaign.scheduled_at,
        subject=initial_step.subject if initial_step else None,
        html_content=initial_step.html_body if initial_step else None,
        plain_content=initial_step.plain_body if initial_step else None,
        followup_count=followup_count,
        steps=ordered_steps,
        general_warmup_delay_value=campaign.general_warmup_delay_value,
        general_warmup_delay_unit=campaign.general_warmup_delay_unit,
    )


@router.post("/{campaign_id}/process-followups")
async def process_followups(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.user_id == current_user.id,
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return await process_campaign_followups(
            campaign_id=campaign_id,
            user_id=current_user.id,
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[CampaignOut])
async def list_campaigns(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == current_user.id)
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
        .offset(skip)
        .limit(limit)
    )
    campaigns = result.scalars().unique().all()
    return [await _campaign_to_out(db, campaign) for campaign in campaigns]


@router.post("", response_model=CampaignOut, status_code=201)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _validate_campaign_group(db, current_user.id, payload.group_id)

    data = payload.model_dump(exclude={"steps"})

    campaign = Campaign(
        user_id=current_user.id,
        **data,
    )
    db.add(campaign)
    await db.flush()

    for step in payload.steps:
        db.add(
            CampaignStep(
                campaign_id=campaign.id,
                step_number=step.step_number,
                step_type=step.step_type,
                name=step.name,
                subject=step.subject,
                html_body=step.html_body,
                plain_body=step.plain_body,
                delay_value=step.delay_value,
                delay_unit=step.delay_unit,
                delay_from=step.delay_from,
                stop_on_reply=step.stop_on_reply,
                is_active=step.is_active,
                wait_after_contact_reply_value=step.wait_after_contact_reply_value,
                wait_after_contact_reply_unit=step.wait_after_contact_reply_unit,
            )
        )

    await _sync_campaign_sender_from_provider(db, campaign, current_user.id)
    await db.commit()

    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign.id)
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
    )
    campaign = result.scalar_one()
    return await _campaign_to_out(db, campaign)


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await _campaign_to_out(db, campaign)


@router.put("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == CampaignStatus.completed:
        raise HTTPException(status_code=400, detail="Cannot edit a completed campaign")

    if "group_id" in payload.model_fields_set:
        await _validate_campaign_group(db, current_user.id, payload.group_id)

    data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
        exclude={"steps"},
    )

    for field, value in data.items():
        setattr(campaign, field, value)

    if payload.steps is not None:
        for step in list(campaign.steps or []):
            await db.delete(step)
        await db.flush()

        for step in payload.steps:
            db.add(
                CampaignStep(
                    campaign_id=campaign.id,
                    step_number=step.step_number,
                    step_type=step.step_type,
                    name=step.name,
                    subject=step.subject,
                    html_body=step.html_body,
                    plain_body=step.plain_body,
                    delay_value=step.delay_value,
                    delay_unit=step.delay_unit,
                    delay_from=step.delay_from,
                    stop_on_reply=step.stop_on_reply,
                    is_active=step.is_active,
                    wait_after_contact_reply_value=step.wait_after_contact_reply_value,
                    wait_after_contact_reply_unit=step.wait_after_contact_reply_unit,
                )
            )

    await _sync_campaign_sender_from_provider(db, campaign, current_user.id)
    await db.commit()

    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign.id)
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
    )
    campaign = result.scalar_one()
    return await _campaign_to_out(db, campaign)


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)
    await db.commit()


@router.post("/{campaign_id}/send")
async def send(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        campaign = await db.get(Campaign, campaign_id)
        if not campaign or campaign.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return await send_campaign(campaign_id, current_user.id, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/start", response_model=CampaignOut)
async def start_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status not in (
        CampaignStatus.draft,
        CampaignStatus.scheduled,
        CampaignStatus.paused,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start campaign in status: {campaign.status}",
        )

    campaign.status = CampaignStatus.running
    await db.commit()
    await db.refresh(campaign)

    return await _campaign_to_out(db, campaign)


@router.post("/{campaign_id}/pause", response_model=CampaignOut)
async def pause_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status != CampaignStatus.running:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause campaign in status: {campaign.status}",
        )

    campaign.status = CampaignStatus.paused
    await db.commit()
    await db.refresh(campaign)

    return await _campaign_to_out(db, campaign)


@router.post("/{campaign_id}/contacts/{contact_id}/reply", status_code=201)
async def record_reply(
    campaign_id: int,
    contact_id: int,
    payload: InboundReplyIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    occurred_at = payload.occurred_at or datetime.now(timezone.utc)

    ev = EmailEvent(
        campaign_id=campaign_id,
        contact_id=contact_id,
        event_type="their_reply",
        occurred_at=occurred_at,
        event_metadata={
            "from_email": payload.from_email,
            "to_email": payload.to_email,
            "subject": payload.subject,
            "text_body": payload.text_body,
            "html_body": payload.html_body,
            "step_id": payload.step_id,
            "step_number": payload.step_number,
        },
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)

    return {"status": "ok", "event_id": ev.id}