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
from app.services.email_service import _render_template, _resolve_send_fn as _resolve_campaign_send_fn


settings = get_settings()
# must exist in your project



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


def _step_due(
    campaign: Campaign,
    step: CampaignStep,
    events: list[EmailEvent],
    now: datetime,
) -> bool:
    # Do not re-send same step
    if _last_step_sent_event(events, step.id):
        return False

    anchor = _anchor_event_for_step(step, events)
    if not anchor or not anchor.occurred_at:
        return False

    # 1) sequence-specific delay: current behavior
    step_due_at = anchor.occurred_at + _delay_delta(step.delay_value, step.delay_unit)

    # 2) general warmup based on last *sent* event in this campaign for this contact
    last_sent_event = _last_event_by_type(events, "sent")
    if last_sent_event and last_sent_event.occurred_at:
        general_td = _delay_delta(
            campaign.general_warmup_delay_value,
            campaign.general_warmup_delay_unit,
        )
        warmup_due_at = last_sent_event.occurred_at + general_td
    else:
        # If we've never sent anything, you can treat general warmup as 0 or anchor-based.
        warmup_due_at = anchor.occurred_at

    # 3) Effective due time is the later of the two
    due_at = max(step_due_at, warmup_due_at)
    return now >= due_at


def _eligible_step_for_contact(
    campaign: Campaign,
    events: list[EmailEvent],
    now: datetime,
) -> Optional[CampaignStep]:
    last_sent_step_number = _last_sent_step_number(events)
    if last_sent_step_number is None:
        return None

    for step in _active_non_initial_steps(campaign):
        if step.step_number <= last_sent_step_number:
            continue

        # stop-after-first-reply rule
        if step.stop_on_reply and _contact_replied(events):
            continue

        # Max normal followups BEFORE any reply
        if step.step_type == StepType.followup and not _contact_replied(events):
            if campaign.max_followups is not None:
                if _normal_followups_count(events) >= campaign.max_followups:
                    continue

        # Max reply followups AFTER last reply
        if step.step_type == StepType.reply_followup:
            if campaign.max_followups is not None:
                if _reply_followups_since_last_reply(events) >= campaign.max_followups:
                    continue

        if _step_due(campaign, step, events, now):
            return step

    return None

    
async def _load_contact_events(campaign_id: int, contact_id: int, db: AsyncSession) -> list[EmailEvent]:
    result = await db.execute(
        select(EmailEvent)
        .where(
            EmailEvent.campaign_id == campaign_id,
            EmailEvent.contact_id == contact_id,
        )
    )
    return result.scalars().all()


                
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





def should_send_normal_followup(
    *,
    contact_has_replied: bool,
    step: CampaignStep,
) -> bool:
    """
    Decide whether a non-reply followup step should be sent to this contact.
    """
    # If contact replied and this step is configured to stop on reply,
    # do NOT send any more normal followups.
    if contact_has_replied and step.stop_on_reply:
        return False

    return True


async def get_contact_has_replied(
    db: AsyncSession,
    campaign_id: int,
    contact_id: int,
) -> bool:
    """
    Returns True if this contact has at least one reply event in this campaign.
    """
    result = await db.execute(
        select(CampaignEvent.id).where(
            CampaignEvent.campaign_id == campaign_id,
            CampaignEvent.contact_id == contact_id,
            CampaignEvent.event_type == "reply",  # adjust to your actual value
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _load_campaign_contacts(
    campaign: Campaign,
    user_id: int,
    db: AsyncSession,
) -> list[Contact]:
    """
    Load all subscribed contacts for this user, filtered by the campaign's segment tags.
    """
    q = select(Contact).where(
        Contact.user_id == user_id,
        Contact.is_subscribed == True,
    )

    if campaign.segment_tags:
        q = q.join(contact_tags).where(
            contact_tags.c.tag_id.in_(campaign.segment_tags)
        )

    result = await db.execute(q)
    return result.scalars().unique().all()

async def _create_run(
    campaign_id: int,
    step_id: Optional[int],
    db: AsyncSession,
) -> CampaignRun:
    """
    Create a CampaignRun row representing this followup processing run.
    """
    run = CampaignRun(
        campaign_id=campaign_id,
        step_id=step_id,
        status=RunStatus.running,
        total_sent=0,
        total_failed=0,
    )
    db.add(run)
    await db.flush()  # populate run.id
    return run


async def _resolve_send_fn(campaign: Campaign, user_id: int, db: AsyncSession):
    """
    Resolve which low-level send function to use (SMTP vs PowerMTA, etc.).
    Delegates to the shared helper from app.services.email_service.
    """
    # you already import _resolve_send_fn at the top:
    # from app.services.email_service import _render_template, _resolve_send_fn
    #
    # so here we just return that helper directly, or wrap it if you need
    # additional per-campaign/per-user logic later.
    return await _resolve_campaign_send_fn(campaign, user_id, db)

async def process_campaign_followups(
    campaign_id: int,
    user_id: int,
    db: AsyncSession,
    step_id: Optional[int] = None,
) -> dict:
    # 1) Load campaign with steps and senders
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

    if campaign.status not in (
        CampaignStatus.running,
        CampaignStatus.paused,
        CampaignStatus.scheduled
    ):
        raise ValueError(
            f"Cannot process followups for campaign in status: {campaign.status}"
        )

    # 2) Load all subscribed contacts for this campaign
    contacts = await _load_campaign_contacts(campaign, user_id, db)
    if not contacts:
        raise ValueError("No subscribed contacts match the campaign segment.")

    # 3) Create a run record for this execution
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

    # Helper: classify one contact into a priority group + next step
    def _classify_contact_state(
        campaign: Campaign,
        events: list[EmailEvent],
        now: datetime,
    ) -> tuple[str | None, Optional[CampaignStep]]:
        """
        Returns a tuple (action_type, step):
          action_type in {"reply", "initial", "reply_followup", "followup"} or None
        """

        # 1) Do we owe them a direct reply? (their_reply newer than our_reply)
        last_their_reply = _last_event_by_type(events, "their_reply")
        last_our_reply = _last_event_by_type(events, "our_reply")
        if last_their_reply and (
            not last_our_reply or last_their_reply.occurred_at > last_our_reply.occurred_at
        ):
            # You might have a dedicated "our_reply" step or template;
            # here we just say we owe a "reply" action with no specific CampaignStep.
            return "reply", None

        # 2) Have we ever sent any email in this campaign to this contact?
        last_sent_step_number = _last_sent_step_number(events)

        if last_sent_step_number is None:
            # No "sent" events → candidate for initial
            initial_step = _initial_step(campaign)
            if _step_due(campaign, initial_step, events, now):
                return "initial", initial_step
            return None, None

        # 3) We have sent something; check reply_followup vs normal followup

        # Find the next reply_followup step that could be due
        next_reply_followup: Optional[CampaignStep] = None
        for step in _active_non_initial_steps(campaign):
            if getattr(step.step_type, "value", step.step_type) != StepType.reply_followup.value:
                continue
            if step.step_number <= last_sent_step_number:
                continue
            if not _step_due(campaign, step, events, now):
                continue
            # Max reply followups after last reply
            if campaign.max_followups is not None:
                if _reply_followups_since_last_reply(events) >= campaign.max_followups:
                    continue
            next_reply_followup = step
            break

        if next_reply_followup:
            return "reply_followup", next_reply_followup

        # 4) Otherwise, consider a normal followup
        next_followup: Optional[CampaignStep] = None
        for step in _active_non_initial_steps(campaign):
            if getattr(step.step_type, "value", step.step_type) != StepType.followup.value:
                continue
            if step.step_number <= last_sent_step_number:
                continue
            if not _step_due(campaign, step, events, now):
                continue
            # stop-after-first-reply rule
            if step.stop_on_reply and _contact_replied(events):
                continue
            # Max normal followups BEFORE any reply
            if campaign.max_followups is not None and not _contact_replied(events):
                if _normal_followups_count(events) >= campaign.max_followups:
                    continue
            next_followup = step
            break

        if next_followup:
            return "followup", next_followup

        return None, None

    # Group contacts into priority buckets
    group_reply: list[tuple[Contact, Optional[CampaignStep]]] = []
    group_initial: list[tuple[Contact, CampaignStep]] = []
    group_reply_followup: list[tuple[Contact, CampaignStep]] = []
    group_followup: list[tuple[Contact, CampaignStep]] = []

    for contact in contacts:
        events = await _load_contact_events(campaign.id, contact.id, db)
        action_type, step = _classify_contact_state(campaign, events, now)

        # Optional step_id filter: only allow given step_id, otherwise ignore
        if step_id is not None and step is not None and step.id != step_id:
            action_type = None
            step = None

        if action_type == "reply":
            group_reply.append((contact, step))
        elif action_type == "initial" and step is not None:
            group_initial.append((contact, step))
        elif action_type == "reply_followup" and step is not None:
            group_reply_followup.append((contact, step))
        elif action_type == "followup" and step is not None:
            group_followup.append((contact, step))
        # else: nothing due

    async def _send_step(contact: Contact, step: CampaignStep):
        nonlocal results, run

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
                run.total_failed = (run.total_failed or 0) + 1
                results["failed"] += 1
                results["errors"].append(str(exc))
                
    # NEW: pick at most one (contact, step) from highest-priority group
    def _pick_next() -> tuple[Optional[Contact], Optional[CampaignStep | None]]:
        # Priority: initials first, then reply, then reply_followup, then followup
        if group_initial:
            return group_initial[0]
        if group_reply:
            return group_reply[0]
        if group_reply_followup:
            return group_reply_followup[0]
        if group_followup:
            return group_followup[0]
        return None, None


    # Helper to process a bucket with your concurrency limit
    async def _process_bucket(bucket: list[tuple[Contact, CampaignStep | None]]):
        for contact, step in bucket:
            if step is None:
                # For "reply" you might have separate handling later
                results["skipped"] += 1
                continue
            await _send_step(contact, step)
            results["processed_contacts"] += 1


    # 5) Process at most ONE contact per call, with priority

    contact, step = _pick_next()

    if contact is not None and step is not None:
        await _send_step(contact, step)
        results["processed_contacts"] += 1
    elif contact is not None and step is None:
        # For "reply" without a specific step, either skip or handle separately
        results["skipped"] += 1
    else:
        # Nothing due for any contact this run
        pass

# 5) Process groups in priority order

# As long as there is any initial work due, do ONLY initials this run.
# if group_initial:
#     await _process_bucket(group_initial)
# else:
#     await _process_bucket(group_reply)           # then direct replies
#     await _process_bucket(group_reply_followup)  # then reply sequences
#     await _process_bucket(group_followup)        # last: normal followups




    run.status = RunStatus.completed
    await db.commit()
    await db.refresh(run)

    return results


def _normal_followups_count(events: list[EmailEvent]) -> int:
    # only until first inbound reply
    first_reply = _first_inbound_reply_event(events)
    cutoff = first_reply.occurred_at if first_reply else None

    count = 0
    for ev in events:
        meta = _event_meta(ev)
        if ev.event_type != "sent":
            continue
        if cutoff and ev.occurred_at >= cutoff:
            continue
        if meta.get("step_type") == "followup":  # your enum/string
            count += 1
    return count    


def _reply_followups_since_last_reply(events: list[EmailEvent]) -> int:
    last_reply = _last_inbound_reply_event(events)
    if not last_reply:
        return 0

    count = 0
    for ev in events:
        meta = _event_meta(ev)
        if ev.event_type != "sent":
            continue
        if ev.occurred_at <= last_reply.occurred_at:
            continue
        if meta.get("step_type") == "reply_followup":
            count += 1
    return count