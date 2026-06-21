from typing import List
import asyncio
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.warmup_task import (
    WarmupTask,
    WarmupDelayUnit,
    WarmupTaskProtocol,
)
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
    WarmupTaskRunViewOut,
)
from app.services.gmail_warmup import (
    collect_gmail_target_for_action,
    execute_gmail_action,
)
from app.services.microsoft_warmup import (
    collect_microsoft_target_for_action,
    execute_microsoft_action,
)
from app.services.imap_warmup import (
    collect_imap_target_for_action,
    execute_imap_action,
)

from app.services.yahoo_warmup import (
    collect_yahoo_target_for_action,
    execute_yahoo_action,
)

router = APIRouter(prefix="/warmup-tasks", tags=["warmup"])


def protocol_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def serialize_task(task: WarmupTask) -> dict:
    protocol_value_str = protocol_value(task.protocol)
    delay_unit_value = (
        task.delay_unit.value if hasattr(task.delay_unit, "value") else task.delay_unit
    )
    oauth_provider = None
    if task.oauth_app:
        oauth_provider = (
            task.oauth_app.provider.value
            if hasattr(task.oauth_app.provider, "value")
            else task.oauth_app.provider
        )

    return {
        "id": task.id,
        "user_id": task.user_id,
        "name": task.name,
        "protocol": protocol_value_str,
        "oauth_app_id": task.oauth_app_id,
        "oauth_app_name": task.oauth_app.name if task.oauth_app else None,
        "oauth_app_provider": oauth_provider,
        "mailbox_ids": task.mailbox_ids or [],
        "do_move_to_inbox": task.do_move_to_inbox,
        "do_open": task.do_open,
        "do_add_to_favorites": task.do_add_to_favorites,
        "do_mark_as_primary": task.do_mark_as_primary,
        "do_reply": task.do_reply,
        "do_campaign_reply": task.do_campaign_reply,
        "do_detect_reply_event": task.do_detect_reply_event,
        "reply_message": task.reply_message,
        "delay_seconds": task.delay_seconds,
        "delay_unit": delay_unit_value,
        "allowed_sender": task.allowed_sender,
        "is_active": task.is_active,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


async def validate_oauth_app_for_create(
    db: AsyncSession,
    current_user: User,
    task_in: WarmupTaskCreate,
) -> OAuthApp | None:
    protocol = protocol_value(task_in.protocol)

    if protocol != "oauth":
        if task_in.oauth_app_id is not None:
            raise HTTPException(
                status_code=400,
                detail="oauth_app_id cannot be set for IMAP warmup tasks",
            )
        return None

    if task_in.oauth_app_id is None:
        raise HTTPException(
            status_code=400,
            detail="oauth_app_id is required for OAuth warmup tasks",
        )

    oauth_stmt = select(OAuthApp).where(
        OAuthApp.id == task_in.oauth_app_id,
        OAuthApp.user_id == current_user.id,
        OAuthApp.is_active.is_(True),
    )
    oauth_res = await db.execute(oauth_stmt)
    oauth_app = oauth_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(
            status_code=404,
            detail="Selected OAuth app was not found",
        )

    return oauth_app


async def validate_mailboxes_for_task(
    db: AsyncSession,
    current_user: User,
    protocol,
    mailbox_ids: list[int],
    oauth_app_id: int | None,
) -> None:
    if not mailbox_ids:
        return

    mailbox_stmt = select(Mailbox).where(
        Mailbox.user_id == current_user.id,
        Mailbox.id.in_(mailbox_ids),
    )
    mailbox_res = await db.execute(mailbox_stmt)
    mailboxes = list(mailbox_res.scalars().all())

    if len(mailboxes) != len(mailbox_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more selected mailboxes were not found",
        )

    protocol_str = protocol_value(protocol)

    if protocol_str == "oauth":
        if oauth_app_id is None:
            raise HTTPException(
                status_code=400,
                detail="oauth_app_id is required for OAuth warmup tasks",
            )

        invalid = [m.id for m in mailboxes if m.oauth_app_id != oauth_app_id]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail="All selected mailboxes must belong to the selected OAuth app",
            )

    elif protocol_str == "imap":
        invalid = []
        for mailbox in mailboxes:
            provider = (
                mailbox.provider.value
                if hasattr(mailbox.provider, "value")
                else mailbox.provider
            )
            provider = (provider or "").lower()

            if mailbox.oauth_app_id is not None:
                invalid.append(mailbox.id)
                continue

            if provider in {"google", "microsoft"}:
                invalid.append(mailbox.id)

        if invalid:
            raise HTTPException(
                status_code=400,
                detail=(
                    "All selected mailboxes must be IMAP mailboxes "
                    "(no OAuth-based Google/Microsoft mailboxes) "
                    "for IMAP warmup tasks"
                ),
            )


def validate_imap_actions(task_in: WarmupTaskCreate) -> None:
    if task_in.do_reply:
        raise HTTPException(
            status_code=400,
            detail="Reply is not supported for IMAP warmup tasks (requires SMTP)",
        )
    if task_in.do_campaign_reply:
        raise HTTPException(
            status_code=400,
            detail="Campaign reply is not supported for IMAP warmup tasks (requires SMTP)",
        )
    if task_in.reply_message:
        raise HTTPException(
            status_code=400,
            detail="reply_message must be empty for IMAP warmup tasks",
        )


def sanitize_imap_actions(task_in: WarmupTaskCreate) -> dict:
    data = task_in.model_dump()
    data["oauth_app_id"] = None
    data["do_reply"] = False
    data["do_campaign_reply"] = False
    data["reply_message"] = None
    return data


async def get_oauth_app_for_task(
    db: AsyncSession,
    current_user: User,
    oauth_app_id: int,
) -> OAuthApp:
    oauth_stmt = select(OAuthApp).where(
        OAuthApp.id == oauth_app_id,
        OAuthApp.user_id == current_user.id,
        OAuthApp.is_active.is_(True),
    )
    oauth_res = await db.execute(oauth_stmt)
    oauth_app = oauth_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(
            status_code=404,
            detail="OAuth app linked to warmup task was not found",
        )

    return oauth_app


@router.get("", response_model=List[WarmupTaskOut])
async def list_warmup_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(WarmupTask)
        .options(selectinload(WarmupTask.oauth_app))
        .where(WarmupTask.user_id == current_user.id)
        .order_by(WarmupTask.id.asc())
    )
    res = await db.execute(stmt)
    tasks = list(res.scalars().all())
    return [serialize_task(task) for task in tasks]


@router.get("/available-oauth-apps")
async def list_available_oauth_apps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_stmt = select(WarmupTask.oauth_app_id).where(
        WarmupTask.user_id == current_user.id,
        WarmupTask.oauth_app_id.is_not(None),
        WarmupTask.protocol == WarmupTaskProtocol.oauth,
    )
    task_res = await db.execute(task_stmt)
    used_oauth_app_ids = [item for item in task_res.scalars().all() if item is not None]

    oauth_stmt = select(OAuthApp).where(
        OAuthApp.user_id == current_user.id,
        OAuthApp.is_active.is_(True),
    )
    if used_oauth_app_ids:
        oauth_stmt = oauth_stmt.where(OAuthApp.id.not_in(used_oauth_app_ids))

    oauth_stmt = oauth_stmt.order_by(OAuthApp.id.desc())
    oauth_res = await db.execute(oauth_stmt)
    oauth_apps = list(oauth_res.scalars().all())

    return [
        {
            "id": app.id,
            "name": getattr(app, "name", None),
            "client_id": getattr(app, "client_id", None),
            "provider": (
                app.provider.value if hasattr(app.provider, "value") else app.provider
            ),
        }
        for app in oauth_apps
    ]


@router.get("/mailboxes-by-oauth-app/{oauth_app_id}")
async def list_mailboxes_by_oauth_app(
    oauth_app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    oauth_stmt = select(OAuthApp).where(
        OAuthApp.id == oauth_app_id,
        OAuthApp.user_id == current_user.id,
        OAuthApp.is_active.is_(True),
    )
    oauth_res = await db.execute(oauth_stmt)
    oauth_app = oauth_res.scalar_one_or_none()

    if not oauth_app:
        raise HTTPException(status_code=404, detail="OAuth app not found")

    mailbox_stmt = (
        select(Mailbox)
        .where(
            Mailbox.user_id == current_user.id,
            Mailbox.oauth_app_id == oauth_app_id,
        )
        .order_by(Mailbox.id.desc())
    )
    mailbox_res = await db.execute(mailbox_stmt)
    mailboxes = list(mailbox_res.scalars().all())

    return [
        {
            "id": mailbox.id,
            "email": mailbox.email,
            "display_name": getattr(mailbox, "display_name", None),
            "provider": (
                mailbox.provider.value
                if hasattr(mailbox.provider, "value")
                else mailbox.provider
            ),
            "oauth_app_id": mailbox.oauth_app_id,
        }
        for mailbox in mailboxes
    ]


@router.get("/imap-mailboxes")
async def list_imap_mailboxes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mailbox_stmt = (
        select(Mailbox)
        .where(Mailbox.user_id == current_user.id)
        .order_by(Mailbox.id.desc())
    )
    mailbox_res = await db.execute(mailbox_stmt)
    mailboxes = list(mailbox_res.scalars().all())

    result = []
    for mailbox in mailboxes:
        provider = (
            mailbox.provider.value if hasattr(mailbox.provider, "value") else mailbox.provider
        )
        provider = (provider or "").lower()

        if mailbox.oauth_app_id is None and provider not in {"google", "microsoft"}:
            result.append(
                {
                    "id": mailbox.id,
                    "email": mailbox.email,
                    "display_name": getattr(mailbox, "display_name", None),
                    "provider": provider,
                    "oauth_app_id": mailbox.oauth_app_id,
                }
            )

    return result


@router.post("", response_model=WarmupTaskOut, status_code=status.HTTP_201_CREATED)
async def create_warmup_task(
    task_in: WarmupTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    protocol = protocol_value(task_in.protocol)

    print("DEBUG protocol:", task_in.protocol, type(task_in.protocol), "oauth_app_id:", task_in.oauth_app_id)

    await validate_oauth_app_for_create(db, current_user, task_in)

    if protocol == "imap":
        validate_imap_actions(task_in)

    await validate_mailboxes_for_task(
        db=db,
        current_user=current_user,
        protocol=task_in.protocol,
        mailbox_ids=task_in.mailbox_ids or [],
        oauth_app_id=task_in.oauth_app_id,
    )

    if protocol == "imap":
        payload = sanitize_imap_actions(task_in)
    else:
        payload = task_in.model_dump()

    task = WarmupTask(
        user_id=current_user.id,
        **payload,
    )
    db.add(task)
    await db.commit()

    stmt = (
        select(WarmupTask)
        .options(selectinload(WarmupTask.oauth_app))
        .where(WarmupTask.id == task.id)
    )
    res = await db.execute(stmt)
    created_task = res.scalar_one()

    return serialize_task(created_task)


@router.put("/{task_id}", response_model=WarmupTaskOut)
async def update_warmup_task(
    task_id: int,
    task_in: WarmupTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(WarmupTask)
        .options(selectinload(WarmupTask.oauth_app))
        .where(
            WarmupTask.id == task_id,
            WarmupTask.user_id == current_user.id,
        )
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Warmup task not found")

    data = task_in.model_dump(exclude_unset=True)

    data.pop("protocol", None)
    data.pop("oauth_app_id", None)

    effective_protocol = protocol_value(task.protocol)
    mailbox_ids = data.get("mailbox_ids", task.mailbox_ids or [])

    if effective_protocol == "oauth":
        await validate_mailboxes_for_task(
            db=db,
            current_user=current_user,
            protocol=effective_protocol,
            mailbox_ids=mailbox_ids,
            oauth_app_id=task.oauth_app_id,
        )
    else:
        if data.get("do_reply") is True:
            raise HTTPException(
                status_code=400,
                detail="Reply is not supported for IMAP warmup tasks (requires SMTP)",
            )
        if data.get("do_campaign_reply") is True:
            raise HTTPException(
                status_code=400,
                detail="Campaign reply is not supported for IMAP warmup tasks (requires SMTP)",
            )
        if data.get("reply_message"):
            raise HTTPException(
                status_code=400,
                detail="reply_message must be empty for IMAP warmup tasks",
            )

        await validate_mailboxes_for_task(
            db=db,
            current_user=current_user,
            protocol=effective_protocol,
            mailbox_ids=mailbox_ids,
            oauth_app_id=None,
        )

        data["oauth_app_id"] = None
        data["do_reply"] = False
        data["do_campaign_reply"] = False
        data["reply_message"] = None

    for key, value in data.items():
        setattr(task, key, value)

    await db.commit()

    stmt = (
        select(WarmupTask)
        .options(selectinload(WarmupTask.oauth_app))
        .where(WarmupTask.id == task.id)
    )
    res = await db.execute(stmt)
    updated_task = res.scalar_one()

    return serialize_task(updated_task)


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

    if protocol_value(task.protocol) == "oauth":
        if task.do_reply or task.do_campaign_reply:
            actions.append(WarmupAction.reply)

    return actions


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
        raise HTTPException(
            status_code=404,
            detail="No valid mailboxes found for this warmup task",
        )

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
    oauth_app: OAuthApp | None,
    action: WarmupAction,
    sender_email: str | None,
) -> str | None:
    provider = (
        mailbox.provider.value if hasattr(mailbox.provider, "value") else mailbox.provider
    )
    provider = (provider or "").lower()

    if provider == "google":
        if not oauth_app:
            raise HTTPException(status_code=400, detail="OAuth app is required for Google warmup")
        return await collect_gmail_target_for_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            sender_email=sender_email,
        )

    if provider == "microsoft":
        if not oauth_app:
            raise HTTPException(status_code=400, detail="OAuth app is required for Microsoft warmup")
        return await collect_microsoft_target_for_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            sender_email=sender_email,
        )

    if provider == "yahoo":
        if not oauth_app:
            raise HTTPException(status_code=400, detail="OAuth app is required for Yahoo warmup")
        return await collect_yahoo_target_for_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            sender_email=sender_email,
        )

    if mailbox.oauth_app_id is None:
        return collect_imap_target_for_action(
            mailbox=mailbox,
            action=action,
            sender_email=sender_email,
        )

    return None


async def execute_action_via_oauth(
    mailbox: Mailbox,
    oauth_app: OAuthApp | None,
    action: WarmupAction,
    target_value: str,
    reply_message: str | None,
) -> None:
    provider = (
        mailbox.provider.value if hasattr(mailbox.provider, "value") else mailbox.provider
    )
    provider = (provider or "").lower()

    if provider == "google":
        if not oauth_app:
            raise HTTPException(status_code=400, detail="OAuth app is required for Google warmup")
        await execute_gmail_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            target_value=target_value,
            reply_message=reply_message,
        )
        return

    if provider == "microsoft":
        if not oauth_app:
            raise HTTPException(status_code=400, detail="OAuth app is required for Microsoft warmup")
        await execute_microsoft_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            target_value=target_value,
            reply_message=reply_message,
        )
        return

    if provider == "yahoo":
        if not oauth_app:
            raise HTTPException(status_code=400, detail="OAuth app is required for Yahoo warmup")
        await execute_yahoo_action(
            mailbox=mailbox,
            oauth_app=oauth_app,
            action=action,
            target_value=target_value,
            reply_message=reply_message,
        )
        return

    if mailbox.oauth_app_id is None:
        execute_imap_action(
            mailbox=mailbox,
            action=action,
            target_value=target_value,
            reply_message=reply_message,
        )
        return

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported provider: {provider}",
    )


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

    oauth_app = None
    if mailbox.oauth_app_id is not None:
        if not task.oauth_app_id:
            raise HTTPException(
                status_code=400,
                detail="Warmup task is not linked to any OAuth app",
            )

        oauth_app = await get_oauth_app_for_task(db, current_user, task.oauth_app_id)

        if mailbox.oauth_app_id != task.oauth_app_id:
            raise HTTPException(
                status_code=400,
                detail="Selected mailbox does not belong to the task OAuth app",
            )

    selected_actions = get_task_allowed_actions(task)
    if not selected_actions:
        raise HTTPException(
            status_code=400,
            detail="No actions are enabled on this warmup task",
        )

    delay_seconds = resolve_delay_seconds(task, payload)
    sender_email = resolve_sender_email(task, payload)
    runid = uuid4().hex

    to_do_tasks: dict[str, str] = {}

    db.add(
        WarmupEvent(
            warmup_task_id=task.id,
            mailbox_id=mailbox.id,
            action=None,
            status=WarmupEventStatus.started,
            detail=f"Task started for {mailbox.email}",
            target_value=None,
            runid=runid,
        )
    )
    await db.commit()

    try:
        for action in selected_actions:
            target_value = await collect_message_for_action(
                mailbox=mailbox,
                oauth_app=oauth_app,
                action=action,
                sender_email=sender_email,
            )
            if target_value:
                to_do_tasks[action.value] = target_value

        if not to_do_tasks:
            db.add(
                WarmupEvent(
                    warmup_task_id=task.id,
                    mailbox_id=mailbox.id,
                    action=None,
                    status=WarmupEventStatus.finished,
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
                status=WarmupEventStatus.started,
                detail=f"Action {action_name} selected for execution",
                target_value=target_value,
                runid=runid,
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)

            try:
                event.status = WarmupEventStatus.running
                event.detail = f"Executing action {action_name}"
                await db.commit()

                await execute_action_via_oauth(
                    mailbox=mailbox,
                    oauth_app=oauth_app,
                    action=action_enum,
                    target_value=target_value,
                    reply_message=task.reply_message,
                )

                event.status = WarmupEventStatus.finished
                event.detail = f"Action {action_name} executed successfully"
                await db.commit()

                executed_actions.append(action_name)

            except HTTPException as exc:
                event.status = WarmupEventStatus.finished_with_error
                event.detail = str(exc.detail)
                await db.commit()
                raise

            except Exception as exc:
                event.status = WarmupEventStatus.finished_with_error
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

    except HTTPException:
        raise


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

        error_statuses = {"error", "failed", "finished_with_error"}

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