import base64
import re
from datetime import datetime
from email.message import EmailMessage
from email.utils import parseaddr

import httpx
from fastapi import HTTPException

from app.models.mailbox import Mailbox
from app.models.oauth_apps import OAuthApp
from app.models.warmup_event import WarmupAction


OLLAMA_URL = "http://ollama:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"


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


def _extract_sender_context(from_header: str | None) -> tuple[str | None, str | None]:
    sender_name, sender_email = parseaddr(from_header or "")
    sender_name = sender_name.strip() or None
    sender_email = sender_email.strip() or None

    if not sender_name and sender_email:
        sender_name = sender_email.split("@", 1)[0]

    return sender_name, sender_email


def _decode_base64url(data: str | None) -> str:
    if not data:
        return ""

    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_plain_text_from_payload(payload: dict | None) -> str:
    if not payload:
        return ""

    mime_type = (payload.get("mimeType") or "").lower()
    body = payload.get("body") or {}
    data = body.get("data")

    if mime_type == "text/plain" and data:
        return _decode_base64url(data).strip()

    parts = payload.get("parts") or []

    for part in parts:
        text = _extract_plain_text_from_payload(part)
        if text.strip():
            return text.strip()

    if data:
        return _decode_base64url(data).strip()

    return ""


async def _generate_with_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        return ""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": cleaned_prompt,
                    "stream": False,
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach Ollama: {str(e)}",
        )

    if res.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama error: {res.text}",
        )

    data = res.json()
    return (data.get("response") or "").strip()


def _format_date_token(token: str, now: datetime) -> str:
    if token == "d":
        return now.strftime("%d")
    if token == "m":
        return now.strftime("%m")
    if token == "y":
        return now.strftime("%Y")
    if token == "D":
        return now.strftime("%A").lower()
    if token == "M":
        return now.strftime("%B").lower()
    if token == "Y":
        return now.strftime("%Y")
    return token


def _format_time_token(token: str, now: datetime) -> str:
    if token == "h":
        return now.strftime("%I")
    if token == "H":
        return now.strftime("%H")
    if token == "m":
        return now.strftime("%M")
    if token == "s":
        return now.strftime("%S")
    return token


def _render_date_placeholder(format_text: str, now: datetime) -> str:
    cleaned = (format_text or "").strip()

    if not cleaned:
        return now.strftime("%d/%m/%Y")

    if any(ch in cleaned for ch in ["h", "H", "s"]):
        parts = [part.strip() for part in cleaned.split(":")]
        return ":".join(_format_time_token(part, now) for part in parts)

    parts = [part.strip() for part in cleaned.split("-")]
    rendered_parts = [_format_date_token(part, now) for part in parts]

    if len(parts) == 3 and parts[0] == "D" and parts[1] == "M" and parts[2] in {"y", "Y"}:
        return f"{rendered_parts[0]}, {rendered_parts[1]} {rendered_parts[2]}"

    return "/".join(rendered_parts)


def _replace_bracket_placeholders(template: str, context: dict[str, str], now: datetime) -> str:
    def repl(match: re.Match) -> str:
        raw_key = (match.group(1) or "").strip()

        if raw_key.startswith("date"):
            parts = raw_key.split("|", 1)
            format_text = parts[1].strip() if len(parts) > 1 else ""
            return _render_date_placeholder(format_text, now)

        if "|" in raw_key:
            key, fallback = raw_key.split("|", 1)
            key = key.strip()
            fallback = fallback.strip()
            value = context.get(key)
            return str(value).strip() if value else fallback

        value = context.get(raw_key)
        return str(value).strip() if value is not None else match.group(0)

    return re.sub(r"\[([^\[\]]+)\]", repl, template)


def _replace_prompt_placeholders(prompt: str, prompt_context: dict[str, str]) -> str:
    result = prompt or ""

    for key, value in prompt_context.items():
        result = result.replace(f"__{key}__", value or "")

    return result


async def _replace_ai_prompts(
    template: str,
    ollama_model: str,
    prompt_context: dict[str, str],
) -> str:
    rebuilt: list[str] = []
    last_end = 0

    for match in re.finditer(r"\$\{(.*?)\}", template, flags=re.DOTALL):
        rebuilt.append(template[last_end:match.start()])

        raw_prompt = match.group(1).strip()
        prompt = raw_prompt.strip("\"'").strip()

        if prompt:
            prompt = _replace_prompt_placeholders(prompt, prompt_context)

            generated_text = await _generate_with_ollama(
                prompt=prompt,
                model=ollama_model,
            )
            rebuilt.append(generated_text)

        last_end = match.end()

    rebuilt.append(template[last_end:])
    return "".join(rebuilt)


async def _render_reply_template(
    template: str,
    sender_name: str | None,
    sender_email: str | None,
    mailbox_email: str | None,
    received_email_body: str | None,
    ollama_model: str = OLLAMA_MODEL,
) -> str:
    result = template or ""
    now = datetime.now()

    context = {
        "sender_name": sender_name or "",
        "sender_email": sender_email or "",
        "mailbox_email": mailbox_email or "",
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M"),
        "datetime": now.strftime("%d/%m/%Y %H:%M"),
    }

    prompt_context = {
        "mail": received_email_body or "",
        "sender_name": sender_name or "",
        "sender_email": sender_email or "",
        "mailbox_email": mailbox_email or "",
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M"),
        "datetime": now.strftime("%d/%m/%Y %H:%M"),
    }

    result = _replace_bracket_placeholders(result, context, now)
    result = await _replace_ai_prompts(
        result,
        ollama_model=ollama_model,
        prompt_context=prompt_context,
    )

    return result.strip()


async def _get_google_access_token(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
) -> str:
    if mailbox.access_token and mailbox.token_expiry:
        from datetime import timedelta

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
            params={"format": "full"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if msg_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch Gmail message: {msg_res.text}",
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

    sender_name, sender_email = _extract_sender_context(original_from)
    received_email_body = _extract_plain_text_from_payload(payload)

    rendered_reply_message = await _render_reply_template(
        template=reply_message,
        sender_name=sender_name,
        sender_email=sender_email,
        mailbox_email=mailbox.email,
        received_email_body=received_email_body,
        ollama_model=OLLAMA_MODEL,
    )

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
    email_msg.set_content(rendered_reply_message)

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