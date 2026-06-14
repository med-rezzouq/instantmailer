from typing import List
import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.warmup_task import WarmupTask, WarmupDelayUnit
from app.models.warmup_event import WarmupEvent, WarmupAction, WarmupEventStatus
from app.models.mailbox import Mailbox
from app.models.oauth_apps import OAuthApp
from app.schemas.warmup import (
    WarmupTaskCreate,
    WarmupTaskUpdate,
    WarmupTaskOut,
    WarmupPerformIn,
    WarmupPerformOut,
    WarmupEventItemOut,
    WarmupRunGroupOut,
    WarmupTaskRunViewOut
)
from app.services.gmail_warmup import (
    collect_gmail_target_for_action,
    execute_gmail_action,
)


router = APIRouter(prefix="/warmup-tasks", tags=["warmup"])


@router.get("", response_model=List[WarmupTaskOut])
async def list_warmup_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(WarmupTask).where(WarmupTask.user_id == current_user.id)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=WarmupTaskOut, status_code=status.HTTP_201_CREATED)
async def create_warmup_task(
    task_in: WarmupTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = WarmupTask(
        user_id=current_user.id,
        **task_in.model_dump(),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/{task_id}", response_model=WarmupTaskOut)
async def update_warmup_task(
    task_id: int,
    task_in: WarmupTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    data = task_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warmup_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    await db.delete(task)
    await db.commit()
    return


def resolve_delay_seconds(task: WarmupTask, payload: WarmupPerformIn) -> int:
    if payload.delay_time is not None:
        if payload.delay_time <= 0:
            raise HTTPException(status_code=400, detail="delay_time must be positive")
        return payload.delay_time

    if task.delay_unit == WarmupDelayUnit.seconds:
        return task.delay_seconds
    if task.delay_unit == WarmupDelayUnit.minutes:
        return task.delay_seconds * 60
    if task.delay_unit == WarmupDelayUnit.hours:
        return task.delay_seconds * 3600

    return task.delay_seconds


def resolve_sender_email(task: WarmupTask, payload: WarmupPerformIn) -> str | None:
    sender = payload.sender_email or task.allowed_sender
    return sender.strip() if sender else None


def get_task_allowed_actions(task: WarmupTask) -> list[WarmupAction]:
    actions: list[WarmupAction] = []

    if task.do_open:
        actions.append(WarmupAction.open)
    if task.do_move_to_inbox:
        actions.append(WarmupAction.move_to_inbox)
    if task.do_add_to_favorites:
        actions.append(WarmupAction.add_to_favorites)
    if task.do_mark_as_primary:
        actions.append(WarmupAction.mark_as_primary)
    if task.do_reply or task.do_campaign_reply:
        actions.append(WarmupAction.reply)

    return actions


def resolve_selected_actions(
    task: WarmupTask,
    payload: WarmupPerformIn,
) -> list[WarmupAction]:
    allowed_actions = get_task_allowed_actions(task)

    if not payload.selected_actions:
        return allowed_actions

    try:
        requested_actions = [WarmupAction(item) for item in payload.selected_actions]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid selected action: {exc}")

    disallowed = [a.value for a in requested_actions if a not in allowed_actions]
    if disallowed:
        raise HTTPException(
            status_code=400,
            detail=f"These actions are not enabled on this warmup task: {', '.join(disallowed)}",
        )

    if WarmupAction.move_to_inbox in requested_actions and WarmupAction.open not in requested_actions:
        requested_actions.insert(0, WarmupAction.open)

    ordered = []
    for action in [
        WarmupAction.open,
        WarmupAction.move_to_inbox,
        WarmupAction.add_to_favorites,
        WarmupAction.mark_as_primary,
        WarmupAction.reply,
    ]:
        if action in requested_actions and action not in ordered:
            ordered.append(action)

    return ordered


async def pick_target_mailbox(
    db: AsyncSession,
    task: WarmupTask,
    user_id: int,
) -> Mailbox:
    mailbox_stmt = select(Mailbox).where(
        Mailbox.user_id == user_id,
        Mailbox.id.in_(task.mailbox_ids),
    )
    mailbox_res = await db.execute(mailbox_stmt)
    mailboxes = list(mailbox_res.scalars().all())

    if not mailboxes:
        raise HTTPException(status_code=404, detail="No valid mailboxes found for this warmup task")

    for mailbox in mailboxes:
        stmt = select(WarmupEvent.id).where(
            WarmupEvent.warmup_task_id == task.id,
            WarmupEvent.mailbox_id == mailbox.id,
        ).limit(1)
        res = await db.execute(stmt)
        found = res.scalar_one_or_none()
        if found is None:
            return mailbox

    event_stmt = (
        select(
            WarmupEvent.mailbox_id,
            func.max(WarmupEvent.created_at).label("last_created_at"),
        )
        .where(
            WarmupEvent.warmup_task_id == task.id,
            WarmupEvent.mailbox_id.in_(task.mailbox_ids),
        )
        .group_by(WarmupEvent.mailbox_id)
        .order_by(func.max(WarmupEvent.created_at).asc())
    )
    event_res = await db.execute(event_stmt)
    first_row = event_res.first()

    if not first_row:
        raise HTTPException(status_code=400, detail="Unable to select mailbox for warmup")

    mailbox_id = first_row.mailbox_id
    selected_mailbox = next((m for m in mailboxes if m.id == mailbox_id), None)

    if not selected_mailbox:
        raise HTTPException(status_code=404, detail="Selected mailbox not found")

    return selected_mailbox


async def collect_message_for_action(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    sender_email: str | None,
) -> str | None:
    if mailbox.provider == "google":
        return await collect_gmail_target_for_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            sender_email=sender_email,
        )

    if mailbox.provider == "microsoft":
        return None

    return None


async def execute_action_via_oauth(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    target_value: str,
    reply_message: str | None,
) -> None:
    if mailbox.provider == "google":
        await execute_gmail_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            target_value=target_value,
            reply_message=reply_message,
        )
        return

    if mailbox.provider == "microsoft":
        return

    raise HTTPException(status_code=400, detail=f"Unsupported provider: {mailbox.provider}")


@router.post("/{task_id}/perform", response_model=WarmupPerformOut)
async def perform_warmup_task(
    task_id: int,
    payload: WarmupPerformIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == current_user.id,
    )
    task_res = await db.execute(task_stmt)
    task = task_res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    if not task.is_active:
        raise HTTPException(status_code=400, detail="Warmup task is not active")

    if not task.mailbox_ids:
        raise HTTPException(status_code=400, detail="Warmup task has no mailboxes")

    mailbox = await pick_target_mailbox(db, task, current_user.id)

    if not mailbox.oauth_app_id:
        raise HTTPException(
            status_code=400,
            detail="Selected mailbox is not linked to any OAuth app",
        )

    oauth_stmt = select(OAuthApp).where(
        OAuthApp.id == mailbox.oauth_app_id,
        OAuthApp.user_id == current_user.id,
        OAuthApp.is_active.is_(True),
    )
    oauth_res = await db.execute(oauth_stmt)
    oauth_app = oauth_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(
            status_code=404,
            detail="OAuth app linked to selected mailbox was not found",
        )

    selected_actions = resolve_selected_actions(task, payload)
    if not selected_actions:
        raise HTTPException(status_code=400, detail="No actions selected")

    delay_seconds = resolve_delay_seconds(task, payload)
    sender_email = resolve_sender_email(task, payload)
    runid = uuid4().hex

    to_do_tasks: dict[str, str] = {}

    for action in selected_actions:
        target_value = await collect_message_for_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            sender_email=sender_email,
        )
        if target_value:
            to_do_tasks[action.value] = target_value

    db.add(
        WarmupEvent(
            warmup_task_id=task.id,
            mailbox_id=mailbox.id,
            action=None,
            status="started",
            detail="Warmup run started",
            target_value=None,
            runid=runid,
        )
    )
    await db.commit()

    if not to_do_tasks:
        db.add(
            WarmupEvent(
                warmup_task_id=task.id,
                mailbox_id=mailbox.id,
                action=None,
                status="finished",
                detail="No unread matching email/message found for this warmup run",
                target_value=None,
                runid=runid,
            )
        )
        await db.commit()

        return WarmupPerformOut(
            ok=True,
            mailbox_id=mailbox.id,
            action=None,
            detail="No unread matching email/message found for this warmup run",
            runid=runid,
        )

    executed_actions: list[str] = []
    items = list(to_do_tasks.items())

    for index, (action_name, target_value) in enumerate(items):
        action_enum = WarmupAction(action_name)

        event = WarmupEvent(
            warmup_task_id=task.id,
            mailbox_id=mailbox.id,
            action=action_enum,
            status="started",
            detail=f"Action {action_name} selected for execution",
            target_value=target_value,
            runid=runid,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        try:
            event.status = "running"
            event.detail = f"Executing action {action_name}"
            await db.commit()

            await execute_action_via_oauth(
                mailbox=mailbox,
                oauth_app=oauth_app,
                action=action_enum,
                target_value=target_value,
                reply_message=task.reply_message,
            )

            event.status = "finished"
            event.detail = f"Action {action_name} executed successfully"
            await db.commit()

            executed_actions.append(action_name)

        except HTTPException as exc:
            event.status = "finished_with_error"
            event.detail = str(exc.detail)
            await db.commit()
            raise

        except Exception as exc:
            event.status = "finished_with_error"
            event.detail = str(exc)
            await db.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error while executing {action_name}: {exc}",
            )

        if index < len(items) - 1:
            await asyncio.sleep(delay_seconds)

    return WarmupPerformOut(
        ok=True,
        mailbox_id=mailbox.id,
        action=", ".join(executed_actions) if executed_actions else None,
        detail="Warmup task executed successfully",
        runid=runid,
    )







@router.get("/taskrun/{task_id}", response_model=WarmupTaskRunViewOut)
async def get_warmup_task_runs(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_stmt = select(WarmupTask).where(
        WarmupTask.id == task_id,
        WarmupTask.user_id == current_user.id,
    )
    task_res = await db.execute(task_stmt)
    task = task_res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    event_stmt = (
        select(WarmupEvent)
        .where(WarmupEvent.warmup_task_id == task.id)
        .order_by(WarmupEvent.created_at.desc(), WarmupEvent.id.desc())
    )
    event_res = await db.execute(event_stmt)
    events = list(event_res.scalars().all())

    grouped: dict[str, list[WarmupEvent]] = {}
    no_run_counter = 0

    for event in events:
        key = event.runid
        if not key:
            no_run_counter += 1
            key = f"legacy-no-runid-{no_run_counter}"
        grouped.setdefault(key, []).append(event)

    def normalize_group_status(items: list[WarmupEvent]) -> str:
        statuses = [
            item.status.value if hasattr(item.status, "value") else str(item.status)
            for item in items
            if item.status
        ]

        error_statuses = {
            "error",
            "failed",
            "finished_with_error",
        }

        if any(status in error_statuses for status in statuses):
            return "finished_with_error"

        non_started_statuses = [status for status in statuses if status != "started"]

        if non_started_statuses and all(status == "finished" for status in non_started_statuses):
            return "finished"

        if any(status == "running" for status in statuses):
            return "running"

        if any(status == "finished" for status in statuses):
            return "finished"

        if any(status == "started" for status in statuses):
            return "started"

        return "unknown"

    runs: list[WarmupRunGroupOut] = []

    for runid, items in grouped.items():
        sorted_items = sorted(items, key=lambda x: (x.created_at, x.id))
        started_at = sorted_items[0].created_at if sorted_items else None
        finished_at = sorted_items[-1].created_at if sorted_items else None

        duration_seconds = None
        if started_at and finished_at:
            duration_seconds = int((finished_at - started_at).total_seconds())

        runs.append(
            WarmupRunGroupOut(
                runid=None if runid.startswith("legacy-no-runid-") else runid,
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=duration_seconds,
                status=normalize_group_status(sorted_items),
                events=[
                    WarmupEventItemOut(
                        id=item.id,
                        warmup_task_id=item.warmup_task_id,
                        mailbox_id=item.mailbox_id,
                        action=item.action.value if item.action else None,
                        status=item.status.value if item.status else None,
                        detail=item.detail,
                        target_value=item.target_value,
                        runid=item.runid,
                        created_at=item.created_at,
                    )
                    for item in sorted_items
                ],
            )
        )

    runs.sort(
        key=lambda r: r.started_at or datetime.min,
        reverse=True,
    )

    return WarmupTaskRunViewOut(
        task_id=task.id,
        runs=runs,
    )