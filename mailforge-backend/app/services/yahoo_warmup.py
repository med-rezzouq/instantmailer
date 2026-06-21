import re
import imaplib
import smtplib
import base64
from email.mime.text import MIMEText
from email.utils import parseaddr
from email.header import decode_header, make_header
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException

from app.models.mailbox import Mailbox
from app.models.oauth_apps import OAuthApp
from app.models.warmup_event import WarmupAction


YAHOO_IMAP_HOST = "imap.mail.yahoo.com"
YAHOO_IMAP_PORT = 993
YAHOO_SMTP_HOST = "smtp.mail.yahoo.com"
YAHOO_SMTP_PORT = 465

OLLAMA_URL = "http://ollama:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"


async def _get_yahoo_access_token(
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
            "https://api.login.yahoo.com/oauth2/get_token",
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
            detail=f"Failed to refresh Yahoo access token: {token_res.text}",
        )

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Yahoo token response missing access_token")

    return access_token


def _build_xoauth2_string(email: str, access_token: str) -> str:
    raw = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_mime_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _extract_text_from_message_bytes(message_bytes: bytes) -> str:
    try:
        import email
        msg = email.message_from_bytes(message_bytes)
    except Exception:
        return ""

    parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = (part.get_content_type() or "").lower()
            disposition = str(part.get("Content-Disposition") or "")
            if "attachment" in disposition.lower():
                continue
            if content_type == "text/plain":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    parts.append(payload.decode(charset, errors="replace"))
                except Exception:
                    parts.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        try:
            parts.append(payload.decode(charset, errors="replace"))
        except Exception:
            parts.append(payload.decode("utf-8", errors="replace"))

    return "\n".join(part.strip() for part in parts if part.strip()).strip()


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


def _imap_login_yahoo(mailbox: Mailbox, access_token: str) -> imaplib.IMAP4_SSL:
    try:
        conn = imaplib.IMAP4_SSL(YAHOO_IMAP_HOST, YAHOO_IMAP_PORT)
        auth_string = f"user={mailbox.email}\x01auth=Bearer {access_token}\x01\x01"
        conn.authenticate("XOAUTH2", lambda _: auth_string.encode("utf-8"))
        return conn
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Yahoo IMAP authentication failed: {exc}")


def _smtp_login_yahoo(mailbox: Mailbox, access_token: str) -> smtplib.SMTP_SSL:
    try:
        smtp = smtplib.SMTP_SSL(YAHOO_SMTP_HOST, YAHOO_SMTP_PORT)
        xoauth2 = _build_xoauth2_string(mailbox.email, access_token)
        code, resp = smtp.docmd("AUTH", "XOAUTH2 " + xoauth2)
        if code != 235:
            raise HTTPException(
                status_code=400,
                detail=f"Yahoo SMTP authentication failed: {code} {resp.decode() if isinstance(resp, bytes) else resp}",
            )
        return smtp
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Yahoo SMTP authentication failed: {exc}")


def _fetch_latest_matching_uid(
    conn: imaplib.IMAP4_SSL,
    sender_email: str | None,
) -> str | None:
    status, _ = conn.select("INBOX")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Could not open Yahoo INBOX")

    criteria = ["UNSEEN"]
    if sender_email:
        criteria.extend(["FROM", f'"{sender_email}"'])

    status, data = conn.search(None, *criteria)
    if status != "OK":
        raise HTTPException(status_code=400, detail="Yahoo IMAP search failed")

    ids = data[0].split() if data and data[0] else []
    if not ids:
        return None

    return ids[-1].decode("utf-8")


def _copy_to_inbox_and_delete(conn: imaplib.IMAP4_SSL, uid: str) -> None:
    status, _ = conn.select('"Bulk"')
    if status != "OK":
        status, _ = conn.select('"Inbox"')
        if status != "OK":
            raise HTTPException(status_code=400, detail="Could not select Yahoo folder for move fallback")

    status, _ = conn.uid("COPY", uid, "INBOX")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Yahoo move to INBOX failed")

    status, _ = conn.uid("STORE", uid, "+FLAGS", r"(\Deleted)")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Yahoo delete-original during move failed")

    conn.expunge()


def _flag_seen(conn: imaplib.IMAP4_SSL, uid: str) -> None:
    status, _ = conn.select("INBOX")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Could not open Yahoo INBOX")

    status, _ = conn.uid("STORE", uid, "+FLAGS", r"(\Seen)")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Yahoo mark-as-read failed")


def _flag_starred(conn: imaplib.IMAP4_SSL, uid: str) -> None:
    status, _ = conn.select("INBOX")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Could not open Yahoo INBOX")

    status, _ = conn.uid("STORE", uid, "+FLAGS", r"(\Flagged)")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Yahoo add-to-favorites failed")


def _fetch_message_metadata(
    conn: imaplib.IMAP4_SSL,
    uid: str,
) -> tuple[str | None, str | None, str | None, str]:
    import email

    status, _ = conn.select("INBOX")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Could not open Yahoo INBOX")

    status, data = conn.uid("FETCH", uid, "(RFC822)")
    if status != "OK" or not data or not data[0]:
        raise HTTPException(status_code=400, detail="Yahoo fetch message failed")

    raw_msg = data[0][1]
    msg = email.message_from_bytes(raw_msg)

    from_header = msg.get("From", "")
    subject = _decode_mime_header(msg.get("Subject"))
    _, sender_email = parseaddr(from_header)
    sender_name = parseaddr(_decode_mime_header(from_header))[0] or None

    if not sender_name and sender_email:
        sender_name = sender_email.split("@", 1)[0]

    body_text = _extract_text_from_message_bytes(raw_msg)

    return sender_name, sender_email or None, subject, body_text


async def collect_yahoo_target_for_action(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    sender_email: str | None,
) -> str | None:
    access_token = await _get_yahoo_access_token(mailbox, oauth_app)
    conn = _imap_login_yahoo(mailbox, access_token)

    try:
        return _fetch_latest_matching_uid(conn, sender_email)
    finally:
        try:
            conn.logout()
        except Exception:
            pass


async def send_yahoo_reply(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    message_id: str,
    reply_message: str,
) -> None:
    if not reply_message or not reply_message.strip():
        raise HTTPException(status_code=400, detail="reply_message is required for reply action")

    access_token = await _get_yahoo_access_token(mailbox, oauth_app)
    conn = _imap_login_yahoo(mailbox, access_token)

    try:
        sender_name, sender_email, subject, received_email_body = _fetch_message_metadata(conn, message_id)
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    rendered_reply_message = await _render_reply_template(
        template=reply_message,
        sender_name=sender_name,
        sender_email=sender_email,
        mailbox_email=mailbox.email,
        received_email_body=received_email_body,
        ollama_model=OLLAMA_MODEL,
    )

    if not sender_email:
        raise HTTPException(status_code=400, detail="Yahoo sender email could not be resolved for reply")

    smtp = _smtp_login_yahoo(mailbox, access_token)

    try:
        msg = MIMEText(rendered_reply_message, "plain", "utf-8")
        msg["Subject"] = f"Re: {subject}" if subject and not subject.lower().startswith("re:") else (subject or "Re:")
        msg["From"] = mailbox.email
        msg["To"] = sender_email
        smtp.sendmail(mailbox.email, [sender_email], msg.as_string())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Yahoo reply send failed: {exc}")
    finally:
        try:
            smtp.quit()
        except Exception:
            pass


async def execute_yahoo_action(
    mailbox: Mailbox,
    oauth_app: OAuthApp,
    action: WarmupAction,
    target_value: str,
    reply_message: str | None,
) -> None:
    access_token = await _get_yahoo_access_token(mailbox, oauth_app)

    if action == WarmupAction.reply:
        await send_yahoo_reply(
            mailbox=mailbox,
            oauth_app=oauth_app,
            message_id=target_value,
            reply_message=reply_message or "",
        )
        return

    if action == WarmupAction.mark_as_primary:
        raise HTTPException(
            status_code=501,
            detail="mark_as_primary is not implemented for Yahoo warmup",
        )

    conn = _imap_login_yahoo(mailbox, access_token)

    try:
        if action == WarmupAction.open:
            _flag_seen(conn, target_value)
            return

        if action == WarmupAction.add_to_favorites:
            _flag_starred(conn, target_value)
            return

        if action == WarmupAction.move_to_inbox:
            _copy_to_inbox_and_delete(conn, target_value)
            return

        raise HTTPException(status_code=400, detail=f"Unsupported Yahoo warmup action: {action.value}")
    finally:
        try:
            conn.logout()
        except Exception:
            pass