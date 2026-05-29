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
from app.services.email_service import (
    _render_template,
    _resolve_send_fn as _resolve_campaign_send_fn,
)

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
    """Generic delay helper used for both step delays and warmup."""
    unit = getattr(delay_unit, "value", delay_unit)
    if unit == "seconds":
        return timedelta(seconds=delay_value)
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
    step = next(
        (
            s
            for s in _ordered_steps(campaign)
            if _step_type_value(s) == StepType.initial.value
        ),
        None,
    )
    if not step:
        raise ValueError("Campaign has no initial step.")
    return step


def _active_non_initial_steps(campaign: Campaign) -> list[CampaignStep]:
    return [
        s
        for s in _ordered_steps(campaign)
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
    return max(
        sent_events,
        key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc),
    )


def _last_event_by_type(events: list[EmailEvent], event_type: str) -> Optional[EmailEvent]:
    filtered = [e for e in events if _normalize_event_type(e.event_type) == event_type]
    if not filtered:
        return None
    return max(
        filtered,
        key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc),
    )


def _last_most_recent_activity(events: list[EmailEvent]) -> Optional[EmailEvent]:
    allowed = {"sent", "their_reply", "our_reply", "opened", "clicked"}
    filtered = [e for e in events if _normalize_event_type(e.event_type) in allowed]
    if not filtered:
        return None
    return max(
        filtered,
        key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc),
    )


def _contact_replied(events: list[EmailEvent]) -> bool:
    return any(_normalize_event_type(e.event_type) == "their_reply" for e in events)


def _last_sent_step_number(events: list[EmailEvent]) -> Optional[int]:
    sent_events = [e for e in events if _normalize_event_type(e.event_type) == "sent"]
    if not sent_events:
        return None

    max_step: Optional[int] = None
    for event in sent_events:
        meta = _event_meta(event)
        step_number = meta.get("step_number")
        if isinstance(step_number, int):
            if max_step is None or step_number > max_step:
                max_step = step_number
    return max_step


def _anchor_event_for_step(step: CampaignStep, all_events: list[EmailEvent]) -> Optional[EmailEvent]:
    delay_from = _delay_from_value(step)
    step_type = _step_type_value(step)

    print(
        "ANCHOR_DEBUG: step.id",
        step.id,
        "step.step_number",
        step.step_number,
        "raw type",
        step.step_type,
        "normalized type",
        step_type,
        "delay_from",
        delay_from,
    )

    # SPECIAL CASE: post_reply_followup anchored on last reply sent
    if step_type == StepType.post_reply_followup.value:
        print("ANCHOR_DEBUG >>> post_reply_followup branch ENTER")
        reply_sents: list[EmailEvent] = []
        for ev in all_events:
            if _normalize_event_type(ev.event_type) != "sent":
                continue
            meta = _event_meta(ev)
            # support both old and new stored values
            if meta.get("step_type") in (StepType.reply.value, "reply_followup"):
                reply_sents.append(ev)

        print("ANCHOR_DEBUG: reply_sents found", len(reply_sents))

        if not reply_sents:
            return None

        anchor = max(
            reply_sents,
            key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc),
        )
        print(
            "ANCHOR_DEBUG: chosen anchor at",
            anchor.occurred_at,
        )
        return anchor

    if delay_from == DelayFrom.previous_step.value:
        # Anchor on the last sent event of the previous step_number
        prev_step_number = (step.step_number or 0) - 1
        if prev_step_number <= 0:
            return None

        prev_sent_events: list[EmailEvent] = []
        for ev in all_events:
            if _normalize_event_type(ev.event_type) != "sent":
                continue
            meta = _event_meta(ev)
            if meta.get("step_number") == prev_step_number:
                prev_sent_events.append(ev)

        print(
            "ANCHOR_DEBUG: previous_step branch, prev_step_number",
            prev_step_number,
            "found",
            len(prev_sent_events),
            "events",
        )

        if not prev_sent_events:
            return None

        anchor = max(
            prev_sent_events,
            key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc),
        )
        print("ANCHOR_DEBUG: previous_step anchor at", anchor.occurred_at)
        return anchor

    if delay_from == DelayFrom.their_reply.value:
        return _last_event_by_type(all_events, "their_reply")

    if delay_from == DelayFrom.our_reply.value:
        return _last_event_by_type(all_events, "our_reply")

    if delay_from == DelayFrom.most_recent.value:
        return _last_most_recent_activity(all_events)

    return None





async def _last_global_sent_event(db: AsyncSession, campaign: Campaign) -> Optional[EmailEvent]:
    result = await db.execute(
        select(EmailEvent)
        .where(EmailEvent.campaign_id == campaign.id,
               EmailEvent.event_type == "sent")
        .order_by(EmailEvent.occurred_at.desc())
        .limit(1)
    )
    return result.scalars().first()


    
def _step_due(
    campaign: Campaign,
    step: CampaignStep,
    events: list[EmailEvent],
    now: datetime,
    *,
    last_global_sent_at: datetime | None,
) -> bool:
    """
    A step is due if:
      - it has not already been sent for this contact, and
      - (for normal steps) its per-contact delay has elapsed from its anchor event, and
      - the general warmup delay (global) has elapsed since the last 'sent' to anyone.

    For reply-anchored steps, we IGNORE per-contact delay for eligibility and only enforce warmup,
    so replies can preempt other work as soon as warmup allows.
    """

    print(
        "STEP_DUE_ENTER",
        "campaign", campaign.id,
        "step", step.step_number, _step_type_value(step),
    )

    step_type = _step_type_value(step)

    # 1) Do not re-send the same step to this contact,
    #    EXCEPT for reply_followup steps which we allow to fire again on new replies.
# 1) Do not re-send the same step to this contact.
    if step_type not in (StepType.post_reply_followup.value, StepType.followup.value):
        if _last_step_sent_event(events, step.id):
            return False

    # 2) Find the anchor event used for this step's own delay
    anchor = _anchor_event_for_step(step, events)

    # Special case: initial step with no events yet -> anchor = now, send immediately
    if _step_type_value(step) == StepType.initial.value and not events:
        anchor = EmailEvent(occurred_at=now)

    if not anchor or not anchor.occurred_at:
        return False

    delay_from = _delay_from_value(step)

    # 3) Per-contact delay from anchor
    if delay_from == DelayFrom.their_reply.value:
        # Replies: ignore per-contact delay for eligibility; only warmup matters
        per_contact_td = timedelta(0)
    else:
        # Normal steps (initial, followups, etc.): use delay_value/unit only
        per_contact_td = _delay_delta(step.delay_value, step.delay_unit)

    step_due_at = anchor.occurred_at + per_contact_td

    # 4) General warmup: from the last global "sent" event (any contact in this campaign)
    if last_global_sent_at is not None:
        general_td = _delay_delta(
            campaign.general_warmup_delay_value,
            campaign.general_warmup_delay_unit,
        )
        warmup_due_at = last_global_sent_at + general_td
    else:
        # No global sends yet; warmup does not hold us back
        warmup_due_at = anchor.occurred_at

    # 5) Final due time is the max of per-contact and warmup
    due_at = max(step_due_at, warmup_due_at)
    result = now >= due_at

    print(
        "STEP_DUE_DEBUG",
        "campaign", campaign.id,
        "step", step.step_number, step_type,
        "events", len(events),
        "now", now.isoformat(),
        "anchor", anchor.occurred_at.isoformat(),
        "per_contact_td", per_contact_td,
        "step_due_at", step_due_at.isoformat(),
        "last_global_sent_at", last_global_sent_at,
        "warmup_td", campaign.general_warmup_delay_value, campaign.general_warmup_delay_unit,
        "warmup_due_at", warmup_due_at.isoformat(),
        "due_at", due_at.isoformat(),
        "result", result,
    )

    return result





async def _load_contact_events(
    campaign_id: int,
    contact_id: int,
    db: AsyncSession,
) -> list[EmailEvent]:
    result = await db.execute(
        select(EmailEvent).where(
            EmailEvent.campaign_id == campaign_id,
            EmailEvent.contact_id == contact_id,
        )
    )
    return result.scalars().all()


async def evaluate_campaign_stop_conditions(db: AsyncSession, campaign: Campaign) -> bool:
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
    if contact_has_replied and step.stop_on_reply:
        return False
    return True


async def _load_campaign_contacts(
    campaign: Campaign,
    user_id: int,
    db: AsyncSession,
) -> list[Contact]:
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


async def _resolve_send_fn(campaign: Campaign, user_id: int, db: AsyncSession):
    base_send_fn = await _resolve_campaign_send_fn(campaign, user_id, db)

    async def send_fn(
        *,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: str = "",
        headers: dict | None = None,
    ):
        return await base_send_fn(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            plain_body=plain_body,
            # headers=headers,
        )

    return send_fn


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

    if campaign.status not in (
        CampaignStatus.running,
        CampaignStatus.paused,
        CampaignStatus.scheduled,
    ):
        raise ValueError(
            f"Cannot process followups for campaign in status: {campaign.status}"
        )

    contacts = await _load_campaign_contacts(campaign, user_id, db)
    print("FOLLOWUPS: contacts loaded", len(contacts))
    if not contacts:
        raise ValueError("No subscribed contacts match the campaign segment.")

    run = await _create_run(campaign.id, step_id, db)
    await db.commit()

    send_fn = await _resolve_send_fn(campaign, user_id, db)
    now = _utcnow()
    semaphore = asyncio.Semaphore(settings.SEND_CONCURRENCY_LIMIT)

    last_global_sent_event = await _last_global_sent_event(db, campaign)
    last_global_sent_at = (
        last_global_sent_event.occurred_at if last_global_sent_event and last_global_sent_event.occurred_at
        else None
    )


    results: dict = {
        "campaign_id": campaign.id,
        "run_id": run.id,
        "processed_contacts": 0,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
        "last_contact_id": None,
    }

    # Helper: classify one contact into a priority group + next step
    def _classify_contact_state(
        campaign: Campaign,
        events: list[EmailEvent],
        now: datetime,
        last_global_sent_at: datetime | None,
    ) -> tuple[str | None, Optional[CampaignStep]]:
        """
        Returns (action_type, step), where action_type is one of:
        - "initial"
        - "initial_followup"   (normal followup before any reply)
        - "normal_reply"       (first reply-followup after last inbound reply)
        - "reply_followup"     (subsequent reply-followups after that)
        or None.
        """

        # 1) Check for fresh inbound reply vs our last manual reply
        last_their_reply = _last_event_by_type(events, "their_reply")
        last_our_reply = _last_event_by_type(events, "our_reply")

        print(
            "CLASSIFY_DEBUG",
            "campaign", campaign.id,
            "events", len(events),
            "last_their_reply", last_their_reply.occurred_at if last_their_reply else None,
            "last_our_reply", last_our_reply.occurred_at if last_our_reply else None,
        )

        contact_has_fresh_reply = (
            last_their_reply
            and (
                not last_our_reply
                or last_their_reply.occurred_at > last_our_reply.occurred_at
            )
        )

        # 2) If they have just replied, prioritize reply-followup steps
        if contact_has_fresh_reply:
            # How many emails have we sent after their LAST reply?
            total_after_reply = _emails_after_last_inbound_reply(events, step_type_filter=None)
            reply_after_reply = _emails_after_last_inbound_reply(events, step_type_filter=StepType.reply.value)
            post_fups_after_reply = _emails_after_last_inbound_reply(events, step_type_filter=StepType.post_reply_followup.value)

            print(
                "REPLY_INTERNAL",
                "total_after_reply", total_after_reply,
                "reply_after_reply", reply_after_reply,
                "post_fups_after_reply", post_fups_after_reply,
            )

            # 2A: Reply sequence (our direct replies after they reply)
            if reply_after_reply < 1:
                next_reply_step: Optional[CampaignStep] = None
                for step in _active_non_initial_steps(campaign):
                    if _step_type_value(step) != StepType.reply.value:
                        continue

                    if not _step_due(
                        campaign,
                        step,
                        events,
                        now,
                        last_global_sent_at=last_global_sent_at,
                    ):
                        continue

                    next_reply_step = step
                    break

                if next_reply_step:
                    # First priority: send reply emails (normal reply sequence)
                    return "normal_reply", next_reply_step

            # 2B: No more reply steps due; consider post-reply followups
            # Here we assume:
            # - We have already replied at least once (reply_after_reply > 0)
            # - They have NOT replied again since then (no extra logic yet; you can plug in helpers later)
            if reply_after_reply > 0:
                next_post_reply_step: Optional[CampaignStep] = None
                for step in _active_non_initial_steps(campaign):
                    if _step_type_value(step) != StepType.post_reply_followup.value:
                        continue

                    if not _step_due(
                        campaign,
                        step,
                        events,
                        now,
                        last_global_sent_at=last_global_sent_at,
                    ):
                        continue

                    # Global cap on post-reply followups per inbound reply
                    max_post_fups = campaign.max_followups  # reuse your field
                    print(
                        "REPLY_CAP_DEBUG campaign",
                        campaign.id,
                        "max_followups raw",
                        campaign.max_followups,
                        "post_fups_after_reply",
                        post_fups_after_reply,
                    )
                    if max_post_fups is not None and post_fups_after_reply >= max_post_fups:
                        print("REPLY_CAP_DEBUG >> hit cap, skipping post_reply_followup for this contact")
                        continue

                    next_post_reply_step = step
                    break

                if next_post_reply_step:
                    return "post_reply_followup", next_post_reply_step

            # Nothing due for this fresh reply
            return None, None



        # 3) No fresh reply: have we ever sent anything?
        last_sent_step_number = _last_sent_step_number(events)

        if last_sent_step_number is None:
            initial_step = _initial_step(campaign)
            if _step_due(
                campaign,
                initial_step,
                events,
                now,
                last_global_sent_at=last_global_sent_at,
            ):
                print(
                    "INIT DUE?",
                    "campaign",
                    campaign.id,
                    "events",
                    len(events),
                    "due",
                    True,
                )
                return "initial", initial_step
            print(
                "INIT DUE?",
                "campaign",
                campaign.id,
                "events",
                len(events),
                "due",
                False,
            )
            return None, None

        # 4) We have sent something; consider normal followups (before any reply)
        next_followup: Optional[CampaignStep] = None
        for step in _active_non_initial_steps(campaign):
            if getattr(step.step_type, "value", step.step_type) != StepType.followup.value:
                continue
            # For normal followups, keep the one-way sequence progression
            # if step.step_number <= last_sent_step_number:
            #     continue
            if not _step_due(
                campaign,
                step,
                events,
                now,
                last_global_sent_at=last_global_sent_at,
            ):
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
            # Initial followup chain before any reply
            return "initial_followup", next_followup

        return None, None



    # Group contacts into priority buckets
    group_initial: list[tuple[Contact, CampaignStep]] = []
    group_initial_followup: list[tuple[Contact, CampaignStep]] = []
    group_normal_reply: list[tuple[Contact, CampaignStep]] = []
    group_reply_followup: list[tuple[Contact, CampaignStep]] = []
    group_post_reply_followup: list[tuple[Contact, CampaignStep]] = []  # NEW

    for contact in contacts:
        events = await _load_contact_events(campaign.id, contact.id, db)
        action_type, step = _classify_contact_state(
            campaign,
            events,
            now,
            last_global_sent_at,
        )

        print(
            "REPLY_CLASSIFY",
            "contact", contact.id,
            "action_type", action_type,
            "step_id", step.id if step else None,
        )    

        # Optional step_id filter
        if step_id is not None and step is not None and step.id != step_id:
            action_type = None
            step = None

        if action_type == "initial" and step is not None:
            group_initial.append((contact, step))
        elif action_type == "initial_followup" and step is not None:
            group_initial_followup.append((contact, step))
        elif action_type == "normal_reply" and step is not None:
            group_normal_reply.append((contact, step))
        elif action_type == "reply_followup" and step is not None:
            group_reply_followup.append((contact, step))
        elif action_type == "post_reply_followup" and step is not None:
            group_post_reply_followup.append((contact, step))
        # else: nothing due

    async def _send_step(contact: Contact, step: CampaignStep):
        nonlocal results, run

        html_body = _render_template(step.html_body, contact)
        plain_body = _render_template(step.plain_body, contact)
        subject = _render_template(step.subject, contact)

        headers = {
            "X-MailForge-Campaign": str(campaign.id),
            "X-MailForge-Contact": str(contact.id),
            "X-MailForge-Step": str(step.id),
            "X-MailForge-Step-Number": str(step.step_number),
            "X-MailForge-Step-Type": _step_type_value(step),
        }

        async with semaphore:
            try:
                await send_fn(
                    to_email=contact.email,
                    subject=subject,
                    html_body=html_body,
                    plain_body=plain_body,
                    # headers=headers,
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
                results["last_contact_id"] = contact.id

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

    # pick at most one (contact, step) from highest-priority group
    def _pick_next() -> tuple[Optional[Contact], Optional[CampaignStep]]:
        # Priority: initial email, then first auto reply,
        # then reply-followups, then post-reply followups, then initial followups
        if group_initial:
            return group_initial[0]
        if group_normal_reply:
            return group_normal_reply[0]
        if group_reply_followup:
            return group_reply_followup[0]
        if group_post_reply_followup:
            return group_post_reply_followup[0]
        if group_initial_followup:
            return group_initial_followup[0]
        return None, None

    # 5) Process at most ONE contact per call
    contact, step = _pick_next()

    if contact is not None and step is not None:
        await _send_step(contact, step)
        results["processed_contacts"] += 1
    else:
        # Nothing due
        pass

    run.status = RunStatus.completed
    await db.commit()
    await db.refresh(run)

    return results


def _first_inbound_reply_event(events: list[EmailEvent]) -> Optional[EmailEvent]:
    replies = [e for e in events if _normalize_event_type(e.event_type) == "their_reply"]
    if not replies:
        return None
    return min(
        replies,
        key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc),
    )





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
        if meta.get("step_type") == "followup":
            count += 1
    return count



def _last_inbound_reply_event(events: list[EmailEvent]) -> Optional[EmailEvent]:
    return _last_event_by_type(events, "their_reply")
    







def _last_outbound_reply_event(events: list[EmailEvent]) -> Optional[EmailEvent]:
    # our manual reply back to the contact
    return _last_event_by_type(events, "our_reply")




def _emails_after_last_inbound_reply(events: list[EmailEvent], *, step_type_filter: str | None = None) -> int:
    """
    Count how many 'sent' events happened AFTER the last inbound reply.
    Optionally filter by step_type.
    """
    last_their_reply = _last_inbound_reply_event(events)
    if not last_their_reply or not last_their_reply.occurred_at:
        return 0

    count = 0
    for ev in events:
        if _normalize_event_type(ev.event_type) != "sent":
            continue
        if not ev.occurred_at or ev.occurred_at <= last_their_reply.occurred_at:
            continue
        meta = _event_meta(ev)
        if step_type_filter is not None:
            if meta.get("step_type") != step_type_filter:
                continue
        count += 1
    return count



def _we_have_replied_to_their_last_reply(events: list[EmailEvent]) -> bool:
    """
    True if there is an 'our_reply' event after the last 'their_reply' event.
    """
    last_their = _last_inbound_reply_event(events)
    last_our = _last_outbound_reply_event(events)

    if not last_their or not last_their.occurred_at:
        return False
    if not last_our or not last_our.occurred_at:
        return False

    return last_our.occurred_at > last_their.occurred_at


def _contact_replied_after_our_last_reply(events: list[EmailEvent]) -> bool:
    """
    True if there is a 'their_reply' after our last 'our_reply'.
    """
    last_their = _last_inbound_reply_event(events)
    last_our = _last_outbound_reply_event(events)

    if not last_our or not last_our.occurred_at:
        return False
    if not last_their or not last_their.occurred_at:
        return False

    return last_their.occurred_at > last_our.occurred_at
