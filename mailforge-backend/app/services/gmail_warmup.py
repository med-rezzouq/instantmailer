import base64
from email.message import EmailMessage

import httpx
from fastapi import HTTPException

from app.models.mailbox import Mailbox
from app.models.oauth_apps import OAuthApp
from app.models.warmup_event import WarmupAction


def _extract_header(headers: list[dict], name: str) -> str | None:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value")
    return None


def _normalize_reply_subject(subject: str | None) -> str:
    if not subject:
        return "Re:"
    if subject.lower().startswith("re:"):
        return subject
    return f"Re: {subject}"


async def _get_google_access_token(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
) -> str:
    if mailbox.access_token and mailbox.token_expiry:
        from datetime import datetime, timedelta

        if mailbox.token_expiry > datetime.utcnow() + timedelta(seconds=60):
            return mailbox.access_token

    if not mailbox.refresh_token:
        raise HTTPException(status_code=400, detail="Mailbox has no refresh token")

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(status_code=400, detail="OAuth app credentials are missing")

    async with httpx.AsyncClient(timeout=30) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": oauth_app.client_id.strip(),
                "client_secret": oauth_app.client_secret.strip(),
                "refresh_token": mailbox.refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to refresh Google access token: {token_res.text}",
        )

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Google token response missing access_token")

    return access_token


async def _modify_gmail_message_labels(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    gmail_message_id: str,
    add_label_ids: list[str] | None = None,
    remove_label_ids: list[str] | None = None,
) -> None:
    access_token = await _get_google_access_token(mailbox, oauth_app)

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{gmail_message_id}/modify",
            json={
                "addLabelIds": add_label_ids or [],
                "removeLabelIds": remove_label_ids or [],
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

    if res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to modify Gmail message labels: {res.text}",
        )


async def send_gmail_reply(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    gmail_message_id: str,
    reply_message: str,
) -> None:
    if not reply_message or not reply_message.strip():
        raise HTTPException(status_code=400, detail="reply_message is required for reply action")

    access_token = await _get_google_access_token(mailbox, oauth_app)

    async with httpx.AsyncClient(timeout=30) as client:
        msg_res = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{gmail_message_id}",
            params={
                "format": "metadata",
                "metadataHeaders": [
                    "From",
                    "To",
                    "Cc",
                    "Reply-To",
                    "Subject",
                    "Message-ID",
                    "References",
                    "In-Reply-To",
                ],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if msg_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch Gmail message metadata: {msg_res.text}",
        )

    msg_data = msg_res.json()
    payload = msg_data.get("payload", {})
    headers = payload.get("headers", [])

    thread_id = msg_data.get("threadId")
    if not thread_id:
        raise HTTPException(status_code=400, detail="Original Gmail message has no threadId")

    original_from = _extract_header(headers, "From")
    reply_to_header = _extract_header(headers, "Reply-To")
    subject = _extract_header(headers, "Subject")
    message_id_header = _extract_header(headers, "Message-ID")
    references_header = _extract_header(headers, "References")

    recipient = reply_to_header or original_from

    if not recipient:
        raise HTTPException(status_code=400, detail="Original Gmail message missing reply destination")

    if not message_id_header:
        raise HTTPException(status_code=400, detail="Original Gmail message missing Message-ID header")

    if references_header:
        references_value = references_header
        if message_id_header not in references_value:
            references_value = f"{references_value} {message_id_header}".strip()
    else:
        references_value = message_id_header

    email_msg = EmailMessage()
    email_msg["To"] = recipient
    email_msg["From"] = mailbox.email
    email_msg["Reply-To"] = mailbox.email
    email_msg["Subject"] = _normalize_reply_subject(subject)
    email_msg["In-Reply-To"] = message_id_header
    email_msg["References"] = references_value
    email_msg.set_content(reply_message.strip())

    raw_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode("utf-8")

    async with httpx.AsyncClient(timeout=30) as client:
        send_res = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            json={
                "raw": raw_message,
                "threadId": thread_id,
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

    if send_res.status_code not in (200, 202):
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send Gmail reply: {send_res.text}",
        )


async def execute_gmail_action(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    target_value: str,
    reply_message: str | None,
) -> None:
    if action == WarmupAction.open:
        await _modify_gmail_message_labels(
            mailbox=mailbox,
            oauth_app=oauth_app,
            gmail_message_id=target_value,
            remove_label_ids=["UNREAD"],
        )
        return

    if action == WarmupAction.move_to_inbox:
        await _modify_gmail_message_labels(
            mailbox=mailbox,
            oauth_app=oauth_app,
            gmail_message_id=target_value,
            add_label_ids=["INBOX"],
            remove_label_ids=["SPAM"],
        )
        return

    if action == WarmupAction.add_to_favorites:
        await _modify_gmail_message_labels(
            mailbox=mailbox,
            oauth_app=oauth_app,
            gmail_message_id=target_value,
            add_label_ids=["STARRED"],
        )
        return

    if action == WarmupAction.mark_as_primary:
        await _modify_gmail_message_labels(
            mailbox=mailbox,
            oauth_app=oauth_app,
            gmail_message_id=target_value,
            add_label_ids=["INBOX"],
            remove_label_ids=[
                "CATEGORY_PROMOTIONS",
                "CATEGORY_SOCIAL",
                "CATEGORY_UPDATES",
                "CATEGORY_FORUMS",
            ],
        )
        return

    if action == WarmupAction.reply:
        await send_gmail_reply(
            mailbox=mailbox,
            oauth_app=oauth_app,
            gmail_message_id=target_value,
            reply_message=reply_message or "",
        )
        return

    raise HTTPException(status_code=400, detail=f"Unsupported Gmail warmup action: {action.value}")


async def collect_gmail_target_for_action(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    sender_email: str | None,
) -> str | None:
    access_token = await _get_google_access_token(mailbox, oauth_app)

    query_parts: list[str] = []
    include_spam_trash = False

    if action == WarmupAction.open:
        query_parts.append("in:anywhere")
        query_parts.append("-in:trash")
        query_parts.append("-in:sent")
        query_parts.append("is:unread")
        include_spam_trash = True

    elif action == WarmupAction.move_to_inbox:
        query_parts.append("in:anywhere")
        query_parts.append("-in:trash")
        query_parts.append("-in:sent")
        query_parts.append("is:unread")
        include_spam_trash = True

    elif action == WarmupAction.add_to_favorites:
        query_parts.append("in:inbox")
        query_parts.append("is:unread")

    elif action == WarmupAction.mark_as_primary:
        query_parts.append("in:inbox")
        query_parts.append("is:unread")

    elif action == WarmupAction.reply:
        query_parts.append("in:inbox")
        query_parts.append("is:unread")

    if sender_email:
        query_parts.append(f"from:{sender_email.strip()}")

    query = " ".join(query_parts) if query_parts else None

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            params={
                "q": query,
                "maxResults": 1,
                "includeSpamTrash": include_spam_trash,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to list Gmail messages: {res.text}",
        )

    data = res.json()
    messages = data.get("messages", [])
    if not messages:
        return None

    return messages[0]["id"]