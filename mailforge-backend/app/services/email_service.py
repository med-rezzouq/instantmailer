import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.analytics import EmailEvent
from app.models.campaign import Campaign, CampaignRecipient, CampaignStatus
from app.models.campaign_step import CampaignStep, StepType
from app.models.contact import Contact, contact_tags
from app.models.oauth_token import OAuthToken, OAuthProvider
from app.models.smtp_config import SMTPConfig
from app.services import microsoft_service, google_service, smtp_service

settings = get_settings()


def _render_template(content: str | None, contact: Contact) -> str:
    if not content:
        return ""
    return (
        content.replace("{{first_name}}", contact.first_name or "")
        .replace("{{last_name}}", contact.last_name or "")
        .replace("{{email}}", contact.email or "")
    )


async def _ensure_fresh_token(token: OAuthToken, db: AsyncSession) -> str:
    now = datetime.now(timezone.utc)
    if token.token_expiry and token.token_expiry <= now:
        if token.provider == OAuthProvider.MICROSOFT:
            data = await microsoft_service.refresh_access_token(token.refresh_token)
        else:
            data = await google_service.refresh_access_token(token.refresh_token)
        token.access_token = data["access_token"]
        await db.commit()
    return token.access_token


async def _resolve_send_fn(campaign: Campaign, user_id: int, db: AsyncSession):
    """
    Resolve a send function for this campaign.

    New flow:
      - Use campaign.provider_id to pick an SMTPConfig for this user.
    Legacy fallback:
      - Use campaign.senders[0] if present.
    """
    smtp_cfg: SMTPConfig | None = None
    sender_type: str | None = None

    # 1) New: if provider_id is set, use that SMTP
    if campaign.provider_id is not None:
        res = await db.execute(
            select(SMTPConfig).where(
                SMTPConfig.user_id == user_id,
                SMTPConfig.id == campaign.provider_id,
                SMTPConfig.is_active == True,
            )
        )
        smtp_cfg = res.scalars().first()
        if smtp_cfg:
            sender_type = "smtp"

    # 2) Legacy fallback: campaign_senders table
    if smtp_cfg is None:
        if not campaign.senders:
            raise ValueError("No sender configured for this campaign.")

        sender: CampaignSender = campaign.senders[0]
        sender_type = getattr(sender.sender_type, "value", sender.sender_type)

        if sender_type == "smtp":
            res = await db.execute(
                select(SMTPConfig).where(
                    SMTPConfig.user_id == user_id,
                    SMTPConfig.id == sender.sender_id,
                    SMTPConfig.is_active == True,
                )
            )
            smtp_cfg = res.scalars().first()
            if not smtp_cfg:
                raise ValueError("No active SMTP configuration found. Add one in Connections.")

    # SMTP branch (either from provider_id or legacy sender)
    if sender_type == "smtp":
        if not smtp_cfg:
            raise ValueError("No active SMTP configuration found. Add one in Connections.")

        async def send_fn(to_email, subject, html_body, plain_body=""):
            return await smtp_service.send_email(
                smtp_cfg,
                to_email,
                subject,
                html_body,
                plain_body,
            )

        return send_fn

    # OAuth-based senders (legacy)
    if sender_type == "microsoft":
        provider_enum = OAuthProvider.MICROSOFT
        send_impl = microsoft_service.send_email
    elif sender_type == "google":
        provider_enum = OAuthProvider.GOOGLE
        send_impl = google_service.send_email
    else:
        raise ValueError(f"Unsupported sender type: {sender_type}")

    res = await db.execute(
        select(OAuthToken).where(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == provider_enum,
        )
    )
    token = res.scalar_one_or_none()
    if not token:
        raise ValueError(f"No {sender_type} account connected.")

    access_token = await _ensure_fresh_token(token, db)

    async def send_fn(to_email, subject, html_body, plain_body=""):
        return await send_impl(
            access_token=access_token,
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            plain_body=plain_body,
        )

    return send_fn


def _get_initial_step(campaign: Campaign) -> CampaignStep:
    ordered_steps = sorted(campaign.steps or [], key=lambda s: s.step_number)
    initial_step = next(
        (
            step for step in ordered_steps
            if getattr(step.step_type, "value", step.step_type) == StepType.initial.value
        ),
        None,
    )
    if not initial_step:
        raise ValueError("Campaign has no initial step.")
    return initial_step


async def send_campaign(campaign_id: int, user_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == user_id)
        .options(
            selectinload(Campaign.steps),
            selectinload(Campaign.senders),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise ValueError("Campaign not found")

    if campaign.status not in (CampaignStatus.draft, CampaignStatus.scheduled, CampaignStatus.paused):
        raise ValueError(f"Cannot send campaign in status: {campaign.status}")

    initial_step = _get_initial_step(campaign)
    send_fn = await _resolve_send_fn(campaign, user_id, db)

    q = select(Contact).where(
        Contact.user_id == user_id,
        Contact.is_subscribed == True,
    )

    if campaign.segment_tags:
        q = q.join(contact_tags).where(contact_tags.c.tag_id.in_(campaign.segment_tags))

    contacts = (await db.execute(q)).scalars().unique().all()

    if not contacts:
        raise ValueError("No subscribed contacts match the campaign segment.")

    semaphore = asyncio.Semaphore(settings.SEND_CONCURRENCY_LIMIT)
    results = {"sent": 0, "failed": 0, "errors": []}

    campaign.status = CampaignStatus.running
    await db.commit()

    async def send_one(contact: Contact):
        html_body = _render_template(initial_step.html_body, contact)
        plain_body = _render_template(initial_step.plain_body, contact)
        subject = _render_template(initial_step.subject, contact)

        async with semaphore:
            try:
                await send_fn(
                    to_email=contact.email,
                    subject=subject,
                    html_body=html_body,
                    plain_body=plain_body,
                )

                db.add(
                    CampaignRecipient(
                        campaign_id=campaign.id,
                        contact_id=contact.id,
                        status="sent",
                        sent_at=datetime.now(timezone.utc),
                    )
                )
                db.add(
                    EmailEvent(
                        campaign_id=campaign.id,
                        contact_id=contact.id,
                        event_type="sent",
                        event_metadata=json.dumps(
                            {
                                "step_id": initial_step.id,
                                "step_number": initial_step.step_number,
                                "step_type": getattr(initial_step.step_type, "value", initial_step.step_type),
                            }
                        ),
                    )
                )
                results["sent"] += 1

            except Exception as exc:
                db.add(
                    CampaignRecipient(
                        campaign_id=campaign.id,
                        contact_id=contact.id,
                        status="failed",
                        error=str(exc),
                    )
                )
                db.add(
                    EmailEvent(
                        campaign_id=campaign.id,
                        contact_id=contact.id,
                        event_type="failed",
                        event_metadata=json.dumps(
                            {
                                "step_id": initial_step.id,
                                "step_number": initial_step.step_number,
                                "step_type": getattr(initial_step.step_type, "value", initial_step.step_type),
                                "error": str(exc),
                            }
                        ),
                    )
                )
                results["failed"] += 1
                results["errors"].append({"contact": contact.email, "error": str(exc)})

    try:
        await asyncio.gather(*[send_one(contact) for contact in contacts])

        campaign.sent_at = datetime.now(timezone.utc)

        if results["sent"] == len(contacts):
            campaign.status = CampaignStatus.completed
        elif results["failed"] == len(contacts):
            campaign.status = CampaignStatus.paused
        else:
            campaign.status = CampaignStatus.completed

        await db.commit()

        return {
            "campaign_id": campaign.id,
            "step_sent": "initial",
            "step_id": initial_step.id,
            "total": len(contacts),
            **results,
        }

    except Exception:
        campaign.status = CampaignStatus.paused
        await db.commit()
        raise