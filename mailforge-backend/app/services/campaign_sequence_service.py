import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.analytics import EmailEvent
from app.models.campaign import Campaign, CampaignRecipient, CampaignStatus
from app.models.campaign_run import CampaignRun, RunStatus
from app.models.campaign_step import CampaignStep, DelayFrom, DelayUnit, StepType
from app.models.contact import Contact, contact_tags
from app.services.email_service import _render_template, _resolve_send_fn

settings = get_settings()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _event_meta(event: EmailEvent) -> dict:
    if isinstance(event.event_metadata, dict):
        return event.event_metadata
    if isinstance(event.event_metadata, str):
        try:
            return json.loads(event.event_metadata)
        except Exception:
            return {}
    return {}


def _normalize_event_type(event_type: str | None) -> str:
    return (event_type or "").strip().lower()


def _delay_delta(delay_value: int, delay_unit: DelayUnit) -> timedelta:
    unit = getattr(delay_unit, "value", delay_unit)
    if unit == "minutes":
        return timedelta(minutes=delay_value)
    if unit == "hours":
        return timedelta(hours=delay_value)
    return timedelta(days=delay_value)


def _step_type_value(step: CampaignStep) -> str:
    return getattr(step.step_type, "value", step.step_type)


def _delay_from_value(step: CampaignStep) -> str:
    return getattr(step.delay_from, "value", step.delay_from)


def _ordered_steps(campaign: Campaign) -> list[CampaignStep]:
    return sorted(campaign.steps or [], key=lambda s: s.step_number)


def _initial_step(campaign: Campaign) -> CampaignStep:
    step = next((s for s in _ordered_steps(campaign) if _step_type_value(s) == StepType.initial.value), None)
    if not step:
        raise ValueError("Campaign has no initial step.")
    return step


def _active_non_initial_steps(campaign: Campaign) -> list[CampaignStep]:
    return [
        s for s in _ordered_steps(campaign)
        if s.is_active and _step_type_value(s) != StepType.initial.value
    ]


def _step_sent_events(events: list[EmailEvent], step_id: int) -> list[EmailEvent]:
    out = []
    for event in events:
        if _normalize_event_type(event.event_type) != "sent":
            continue
        meta = _event_meta(event)
        if meta.get("step_id") == step_id:
            out.append(event)
    return out


def _last_step_sent_event(events: list[EmailEvent], step_id: int) -> Optional[EmailEvent]:
    sent_events = _step_sent_events(events, step_id)
    if not sent_events:
        return None
    return max(sent_events, key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc))


def _last_event_by_type(events: list[EmailEvent], event_type: str) -> Optional[EmailEvent]:
    filtered = [e for e in events if _normalize_event_type(e.event_type) == event_type]
    if not filtered:
        return None
    return max(filtered, key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc))


def _last_most_recent_activity(events: list[EmailEvent]) -> Optional[EmailEvent]:
    allowed = {"sent", "their_reply", "our_reply", "opened", "clicked"}
    filtered = [e for e in events if _normalize_event_type(e.event_type) in allowed]
    if not filtered:
        return None
    return max(filtered, key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc))


def _contact_replied(events: list[EmailEvent]) -> bool:
    return any(_normalize_event_type(e.event_type) == "their_reply" for e in events)


def _last_sent_step_number(events: list[EmailEvent]) -> Optional[int]:
    sent_events = [e for e in events if _normalize_event_type(e.event_type) == "sent"]
    if not sent_events:
        return None

    max_step = None
    for event in sent_events:
        meta = _event_meta(event)
        step_number = meta.get("step_number")
        if isinstance(step_number, int):
            if max_step is None or step_number > max_step:
                max_step = step_number
    return max_step


def _anchor_event_for_step(step: CampaignStep, all_events: list[EmailEvent]) -> Optional[EmailEvent]:
    delay_from = _delay_from_value(step)

    if delay_from == DelayFrom.previous_step.value:
        previous_step_number = step.step_number - 1
        previous_sent = []
        for event in all_events:
            if _normalize_event_type(event.event_type) != "sent":
                continue
            meta = _event_meta(event)
            if meta.get("step_number") == previous_step_number:
                previous_sent.append(event)
        if not previous_sent:
            return None
        return max(previous_sent, key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc))

    if delay_from == DelayFrom.their_reply.value:
        return _last_event_by_type(all_events, "their_reply")

    if delay_from == DelayFrom.our_reply.value:
        return _last_event_by_type(all_events, "our_reply")

    if delay_from == DelayFrom.most_recent.value:
        return _last_most_recent_activity(all_events)

    return None


def _step_due(step: CampaignStep, events: list[EmailEvent], now: datetime) -> bool:
    if _last_step_sent_event(events, step.id):
        return False

    anchor = _anchor_event_for_step(step, events)
    if not anchor or not anchor.occurred_at:
        return False

    due_at = anchor.occurred_at + _delay_delta(step.delay_value, step.delay_unit)
    return now >= due_at


def _eligible_step_for_contact(campaign: Campaign, events: list[EmailEvent], now: datetime) -> Optional[CampaignStep]:
    last_sent_step_number = _last_sent_step_number(events)
    if last_sent_step_number is None:
        return None

    for step in _active_non_initial_steps(campaign):
        if step.step_number <= last_sent_step_number:
            continue

        if step.stop_on_reply and _contact_replied(events):
            continue

        if _step_due(step, events, now):
            return step

    return None


async def _load_campaign_contacts(campaign: Campaign, user_id: int, db: AsyncSession) -> list[Contact]:
    q = select(Contact).where(
        Contact.user_id == user_id,
        Contact.is_subscribed == True,
    )

    if campaign.segment_tags:
        q = q.join(contact_tags).where(contact_tags.c.tag_id.in_(campaign.segment_tags))

    return (await db.execute(q)).scalars().unique().all()


async def _load_contact_events(campaign_id: int, contact_id: int, db: AsyncSession) -> list[EmailEvent]:
    result = await db.execute(
        select(EmailEvent)
        .where(
            EmailEvent.campaign_id == campaign_id,
            EmailEvent.contact_id == contact_id,
        )
    )
    return result.scalars().all()


async def _create_run(campaign_id: int, step_id: Optional[int], db: AsyncSession) -> CampaignRun:
    run = CampaignRun(
        campaign_id=campaign_id,
        step_id=step_id,
        status=RunStatus.running,
        total_sent=0,
        total_failed=0,
    )
    db.add(run)
    await db.flush()
    return run


async def process_campaign_followups(
    campaign_id: int,
    user_id: int,
    db: AsyncSession,
    step_id: Optional[int] = None,
) -> dict:
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

    if campaign.status not in (CampaignStatus.running, CampaignStatus.paused, CampaignStatus.scheduled):
        raise ValueError(f"Cannot process followups for campaign in status: {campaign.status}")

    contacts = await _load_campaign_contacts(campaign, user_id, db)
    if not contacts:
        raise ValueError("No subscribed contacts match the campaign segment.")

    run = await _create_run(campaign.id, step_id, db)
    await db.commit()

    send_fn = await _resolve_send_fn(campaign, user_id, db)
    now = _utcnow()
    semaphore = asyncio.Semaphore(settings.SEND_CONCURRENCY_LIMIT)

    results = {
        "campaign_id": campaign.id,
        "run_id": run.id,
        "processed_contacts": 0,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
    }

    async def process_one(contact: Contact):
        nonlocal results, run
        events = await _load_contact_events(campaign.id, contact.id, db)
        step = _eligible_step_for_contact(campaign, events, now)

        if step_id is not None and step and step.id != step_id:
            step = None

        if not step:
            results["skipped"] += 1
            return

        html_body = _render_template(step.html_body, contact)
        plain_body = _render_template(step.plain_body, contact)
        subject = _render_template(step.subject, contact)

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
                        sent_at=_utcnow(),
                    )
                )
                db.add(
                    EmailEvent(
                        campaign_id=campaign.id,
                        contact_id=contact.id,
                        event_type="sent",
                        event_metadata={
                            "step_id": step.id,
                            "step_number": step.step_number,
                            "step_type": _step_type_value(step),
                            "direction": "outbound",
                        },
                    )
                )

                run.total_sent = (run.total_sent or 0) + 1
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
                
async def evaluate_campaign_stop_conditions(db, campaign):
    if campaign.max_bounces is not None and campaign.bounce_count >= campaign.max_bounces:
        campaign.status = CampaignStatus.stopped
        campaign.stopped_by_condition = True
        campaign.stop_reason = "max_bounces_reached"
        await db.commit()
        return True

    if campaign.max_complaints is not None and campaign.complaint_count >= campaign.max_complaints:
        campaign.status = CampaignStatus.stopped
        campaign.stopped_by_condition = True
        campaign.stop_reason = "max_complaints_reached"
        await db.commit()
        return True

    if campaign.max_unsubscribes is not None and campaign.unsubscribe_count >= campaign.max_unsubscribes:
        campaign.status = CampaignStatus.stopped
        campaign.stopped_by_condition = True
        campaign.stop_reason = "max_unsubscribes_reached"
        await db.commit()
        return True

    return False