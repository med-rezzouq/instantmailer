import re
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException

from app.models.mailbox import Mailbox
from app.models.oauth_apps import OAuthApp
from app.models.warmup_event import WarmupAction


GRAPH_BASE = "https://graph.microsoft.com/v1.0"
OLLAMA_URL = "http://ollama:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"


async def _get_microsoft_access_token(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
) -> str:
    if mailbox.access_token and mailbox.token_expiry:
        if mailbox.token_expiry > datetime.utcnow() + timedelta(seconds=60):
            return mailbox.access_token

    if not mailbox.refresh_token:
        raise HTTPException(status_code=400, detail="Mailbox has no refresh token")

    if not oauth_app.client_id or not oauth_app.client_secret:
        raise HTTPException(status_code=400, detail="OAuth app credentials are missing")

    async with httpx.AsyncClient(timeout=30) as client:
        token_res = await client.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
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
            detail=f"Failed to refresh Microsoft access token: {token_res.text}",
        )

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Microsoft token response missing access_token")

    return access_token


async def _graph_get(
    access_token: str,
    path: str,
    params: dict | None = None,
    extra_headers: dict | None = None,
) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    if extra_headers:
        headers.update(extra_headers)

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(
            f"{GRAPH_BASE}{path}",
            params=params,
            headers=headers,
        )

    if res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Microsoft Graph GET failed: {res.text}")

    return res.json()


async def _graph_patch(
    access_token: str,
    path: str,
    payload: dict,
) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.patch(
            f"{GRAPH_BASE}{path}",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

    if res.status_code not in (200, 202):
        raise HTTPException(status_code=400, detail=f"Microsoft Graph PATCH failed: {res.text}")


async def _graph_post(
    access_token: str,
    path: str,
    payload: dict | None = None,
) -> dict | None:
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            f"{GRAPH_BASE}{path}",
            json=payload or {},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

    if res.status_code not in (200, 201, 202):
        raise HTTPException(status_code=400, detail=f"Microsoft Graph POST failed: {res.text}")

    if not res.text.strip():
        return None
    return res.json()


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


async def _get_inbox_folder_id(access_token: str) -> str:
    data = await _graph_get(access_token, "/me/mailFolders/inbox")
    folder_id = data.get("id")
    if not folder_id:
        raise HTTPException(status_code=400, detail="Inbox folder not found")
    return folder_id


async def _get_microsoft_message_for_reply(access_token: str, message_id: str) -> dict:
    return await _graph_get(
        access_token,
        f"/me/messages/{message_id}",
        params={
            "$select": "id,subject,from,replyTo,body,uniqueBody,receivedDateTime",
        },
        extra_headers={
            "Prefer": 'outlook.body-content-type="text"',
        },
    )


async def collect_microsoft_target_for_action(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    sender_email: str | None,
) -> str | None:
    access_token = await _get_microsoft_access_token(mailbox, oauth_app)

    filters = ["receivedDateTime ge 1900-01-01T00:00:00Z", "isRead eq false"]

    if sender_email:
        sender_email = sender_email.strip().replace("'", "''").lower()
        filters.append(f"from/emailAddress/address eq '{sender_email}'")

    if action == WarmupAction.mark_as_primary:
        filters.append("inferenceClassification ne 'focused'")

    filter_query = " and ".join(filters)

    data = await _graph_get(
        access_token,
        "/me/messages",
        params={
            "$top": 1,
            "$orderby": "receivedDateTime desc",
            "$filter": filter_query,
            "$select": "id,parentFolderId,isRead,inferenceClassification,receivedDateTime,from",
        },
    )

    items = data.get("value", [])
    if not items:
        return None

    return items[0]["id"]


async def send_microsoft_reply(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    message_id: str,
    reply_message: str,
) -> None:
    if not reply_message or not reply_message.strip():
        raise HTTPException(status_code=400, detail="reply_message is required for reply action")

    access_token = await _get_microsoft_access_token(mailbox, oauth_app)

    original_message = await _get_microsoft_message_for_reply(access_token, message_id)

    from_obj = original_message.get("from") or {}
    from_email_obj = from_obj.get("emailAddress") or {}

    sender_name = (from_email_obj.get("name") or "").strip() or None
    sender_email = (from_email_obj.get("address") or "").strip() or None

    if not sender_name and sender_email:
        sender_name = sender_email.split("@", 1)[0]

    received_email_body = (
        ((original_message.get("uniqueBody") or {}).get("content")) or
        ((original_message.get("body") or {}).get("content")) or
        ""
    ).strip()

    rendered_reply_message = await _render_reply_template(
        template=reply_message,
        sender_name=sender_name,
        sender_email=sender_email,
        mailbox_email=mailbox.email,
        received_email_body=received_email_body,
        ollama_model=OLLAMA_MODEL,
    )

    await _graph_post(
        access_token,
        f"/me/messages/{message_id}/reply",
        {
            "comment": rendered_reply_message.strip(),
        },
    )


async def execute_microsoft_action(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    target_value: str,
    reply_message: str | None,
) -> None:
    access_token = await _get_microsoft_access_token(mailbox, oauth_app)

    if action == WarmupAction.open:
        await _graph_patch(
            access_token,
            f"/me/messages/{target_value}",
            {"isRead": True},
        )
        return

    if action == WarmupAction.add_to_favorites:
        await _graph_patch(
            access_token,
            f"/me/messages/{target_value}",
            {"flag": {"flagStatus": "flagged"}},
        )
        return

    if action == WarmupAction.move_to_inbox:
        inbox_id = await _get_inbox_folder_id(access_token)
        await _graph_post(
            access_token,
            f"/me/messages/{target_value}/move",
            {"destinationId": inbox_id},
        )
        return

    if action == WarmupAction.mark_as_primary:
        await _graph_patch(
            access_token,
            f"/me/messages/{target_value}",
            {"inferenceClassification": "focused"},
        )
        return

    if action == WarmupAction.reply:
        await send_microsoft_reply(
            mailbox=mailbox,
            oauth_app=oauth_app,
            message_id=target_value,
            reply_message=reply_message or "",
        )
        return

    raise HTTPException(status_code=400, detail=f"Unsupported Microsoft warmup action: {action.value}")