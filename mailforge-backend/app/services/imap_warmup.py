import email
import imaplib
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr

from fastapi import HTTPException

from app.models.mailbox import Mailbox
from app.models.warmup_event import WarmupAction


INBOX_FOLDER = "INBOX"
COMMON_SPAM_FOLDERS = [
    "[Gmail]/Spam",
    "Spam",
    "Junk",
    "Junk E-mail",
    "Bulk Mail",
]


def _quote_imap_mailbox(name: str) -> str:
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _connect_imap(mailbox: Mailbox) -> imaplib.IMAP4:
    try:
        if mailbox.imap_ssl:
            client = imaplib.IMAP4_SSL(mailbox.imap_host, mailbox.imap_port)
        else:
            client = imaplib.IMAP4(mailbox.imap_host, mailbox.imap_port)

        client.login(mailbox.username, mailbox.password)
        return client
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"IMAP connection failed: {exc}")


def _connect_smtp(mailbox: Mailbox) -> smtplib.SMTP:
    try:
        if not mailbox.smtp_host or not mailbox.smtp_port:
            raise HTTPException(status_code=400, detail="SMTP is not configured for this mailbox")

        if mailbox.smtp_tls:
            context = ssl.create_default_context()
            client = smtplib.SMTP(mailbox.smtp_host, mailbox.smtp_port, timeout=30)
            client.ehlo()
            client.starttls(context=context)
            client.ehlo()
        else:
            client = smtplib.SMTP_SSL(
                mailbox.smtp_host,
                mailbox.smtp_port,
                timeout=30,
                context=ssl.create_default_context(),
            )

        client.login(mailbox.username, mailbox.password)
        return client
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"SMTP connection failed: {exc}")


def _list_mailboxes(client: imaplib.IMAP4) -> list[str]:
    status, data = client.list()
    if status != "OK":
        return []

    names: list[str] = []
    for raw in data or []:
        line = raw.decode(errors="ignore")
        if ' "/" ' in line:
            parts = line.split(' "/" ', 1)
        else:
            parts = line.rsplit(" ", 1)

        if len(parts) == 2:
            name = parts[1].strip()
            if name.startswith('"') and name.endswith('"'):
                name = name[1:-1]
            names.append(name)

    return names


def _select_folder(client: imaplib.IMAP4, folder_name: str, readonly: bool = False) -> bool:
    status, _ = client.select(_quote_imap_mailbox(folder_name), readonly=readonly)
    return status == "OK"


def _find_existing_spam_folder(client: imaplib.IMAP4) -> str | None:
    available = _list_mailboxes(client)
    lowered = {name.lower(): name for name in available}

    for candidate in COMMON_SPAM_FOLDERS:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]

    for name in available:
        low = name.lower()
        if "spam" in low or "junk" in low:
            return name

    return None


def _build_search_criteria(sender_email: str | None, unseen_only: bool = True) -> str:
    criteria_parts: list[str] = []
    if unseen_only:
        criteria_parts.append("UNSEEN")
    if sender_email:
        safe_sender = sender_email.strip().replace('"', "")
        criteria_parts.extend(["FROM", f'"{safe_sender}"'])

    if not criteria_parts:
        return "ALL"

    return f"({' '.join(criteria_parts)})"


def _search_first_message_in_folder(
    client: imaplib.IMAP4,
    folder_name: str,
    criteria: str,
) -> str | None:
    if not _select_folder(client, folder_name, readonly=False):
        return None

    status, data = client.uid("SEARCH", None, criteria)
    if status != "OK":
        raise HTTPException(status_code=400, detail=f"Failed to search IMAP messages in {folder_name}")

    ids = (data[0] or b"").split()
    if not ids:
        return None

    return ids[-1].decode()


def _fetch_message_bytes(client: imaplib.IMAP4, folder_name: str, uid: str) -> bytes:
    if not _select_folder(client, folder_name, readonly=False):
        raise HTTPException(status_code=400, detail=f"Failed to select folder {folder_name}")

    status, data = client.uid("FETCH", uid, "(RFC822)")
    if status != "OK" or not data or not data[0]:
        raise HTTPException(status_code=400, detail="Failed to fetch original message")

    payload = data[0][1]
    if not payload:
        raise HTTPException(status_code=400, detail="Original message payload is empty")

    return payload


def _decode_subject(raw_subject: str | None) -> str:
    if not raw_subject:
        return ""
    decoded_parts = email.header.decode_header(raw_subject)
    result = []
    for value, charset in decoded_parts:
        if isinstance(value, bytes):
            result.append(value.decode(charset or "utf-8", errors="ignore"))
        else:
            result.append(value)
    return "".join(result).strip()


def _extract_text_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/plain" and "attachment" not in disposition.lower():
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="ignore").strip()

        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/html" and "attachment" not in disposition.lower():
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                html = payload.decode(charset, errors="ignore")
                return html.strip()

        return ""

    payload = msg.get_payload(decode=True) or b""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="ignore").strip()


def _fetch_original_message_metadata(
    client: imaplib.IMAP4,
    folder_name: str,
    uid: str,
) -> dict:
    raw_bytes = _fetch_message_bytes(client, folder_name, uid)
    msg = email.message_from_bytes(raw_bytes)

    from_name, from_email = parseaddr(msg.get("From", ""))
    subject = _decode_subject(msg.get("Subject"))
    message_id = (msg.get("Message-ID") or "").strip()
    references = (msg.get("References") or "").strip()
    in_reply_to = (msg.get("In-Reply-To") or "").strip()
    body = _extract_text_body(msg)

    return {
        "from_name": from_name.strip(),
        "from_email": from_email.strip(),
        "subject": subject,
        "message_id": message_id,
        "references": references,
        "in_reply_to": in_reply_to,
        "body": body,
    }


def _move_message_between_folders(
    client: imaplib.IMAP4,
    uid: str,
    source_folder: str,
    destination_folder: str,
) -> None:
    if not _select_folder(client, source_folder, readonly=False):
        raise HTTPException(status_code=400, detail=f"Failed to select source folder {source_folder}")

    status, _ = client.uid("COPY", uid, _quote_imap_mailbox(destination_folder))
    if status != "OK":
        raise HTTPException(status_code=400, detail=f"Failed to copy message to {destination_folder}")

    status, _ = client.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
    if status != "OK":
        raise HTTPException(
            status_code=400,
            detail="Failed to mark source message deleted after copy",
        )

    client.expunge()


def _set_flagged(client: imaplib.IMAP4, folder_name: str, uid: str) -> None:
    if not _select_folder(client, folder_name, readonly=False):
        raise HTTPException(status_code=400, detail=f"Failed to select folder {folder_name}")

    status, _ = client.uid("STORE", uid, "+FLAGS", "(\\Flagged)")
    if status != "OK":
        raise HTTPException(status_code=400, detail="Failed to flag message")

        

def collect_imap_target_for_action(
    mailbox: Mailbox,
    action: WarmupAction,
    sender_email: str | None,
    include_spam: bool = False,
) -> str | None:
    client = _connect_imap(mailbox)
    try:
        criteria = _build_search_criteria(sender_email=sender_email, unseen_only=True)

        provider = (
            mailbox.provider.value if hasattr(mailbox.provider, "value") else mailbox.provider
        )
        provider = (provider or "").lower()
        imap_host = (mailbox.imap_host or "").lower()
        email_addr = (mailbox.email or mailbox.username or "").lower()

        is_gmail = (
            provider == "google"
            or "gmail" in imap_host
            or email_addr.endswith("@gmail.com")
        )

        is_outlook = (
            provider == "microsoft"
            or "outlook" in imap_host
            or "office365" in imap_host
            or email_addr.endswith("@outlook.com")
            or email_addr.endswith("@hotmail.com")
            or email_addr.endswith("@live.com")
        )

        candidate_folders: list[str] = [INBOX_FOLDER]

        if is_gmail:
            candidate_folders.extend([
                "[Gmail]/Important",
                "[Gmail]/All Mail",
            ])
        elif is_outlook:
            candidate_folders.extend([
                "Junk",
                "Junk E-mail",
            ])

        if include_spam or action == WarmupAction.move_to_inbox:
            spam_folder = _find_existing_spam_folder(client)
            if spam_folder and spam_folder not in candidate_folders:
                candidate_folders.append(spam_folder)

        seen = set()
        deduped_folders: list[str] = []
        for folder in candidate_folders:
            key = folder.lower()
            if key not in seen:
                deduped_folders.append(folder)
                seen.add(key)

        for folder_name in deduped_folders:
            uid = _search_first_message_in_folder(client, folder_name, criteria)
            if uid:
                return f"{folder_name}::{uid}"

        return None
    finally:
        try:
            client.logout()
        except Exception:
            pass


def _split_target_value(target_value: str) -> tuple[str, str]:
    if "::" in target_value:
        folder_name, uid = target_value.split("::", 1)
        return folder_name, uid
    return INBOX_FOLDER, target_value


def _send_reply_via_smtp(
    mailbox: Mailbox,
    to_email: str,
    original_subject: str,
    original_message_id: str,
    original_references: str,
    reply_message: str,
) -> None:
    if not reply_message or not reply_message.strip():
        raise HTTPException(status_code=400, detail="reply_message is required for reply action")

    msg = EmailMessage()
    msg["From"] = mailbox.email or mailbox.username
    msg["To"] = to_email
    msg["Subject"] = original_subject if original_subject.lower().startswith("re:") else f"Re: {original_subject}"
    msg["In-Reply-To"] = original_message_id

    references = original_references.strip()
    if references:
        msg["References"] = f"{references} {original_message_id}".strip()
    else:
        msg["References"] = original_message_id

    msg.set_content(reply_message.strip())

    smtp_client = _connect_smtp(mailbox)
    try:
        smtp_client.send_message(msg)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to send SMTP reply: {exc}")
    finally:
        try:
            smtp_client.quit()
        except Exception:
            pass



def execute_imap_action(
    mailbox: Mailbox,
    action: WarmupAction,
    target_value: str,
    reply_message: str | None,
) -> None:
    client = _connect_imap(mailbox)
    try:
        folder_name, uid = _split_target_value(target_value)

        if action == WarmupAction.open:
            if not _select_folder(client, folder_name, readonly=False):
                raise HTTPException(status_code=400, detail=f"Failed to select folder {folder_name}")

            status, _ = client.uid("STORE", uid, "+FLAGS", "(\\Seen)")
            if status != "OK":
                raise HTTPException(status_code=400, detail="Failed to mark message as read")
            return

        if action == WarmupAction.add_to_favorites:
            _set_flagged(client, folder_name, uid)
            return

        if action == WarmupAction.move_to_inbox:
            if folder_name.upper() == INBOX_FOLDER:
                return
            _move_message_between_folders(client, uid, folder_name, INBOX_FOLDER)
            return

        if action == WarmupAction.mark_as_primary:
            _set_flagged(client, folder_name, uid)
            return

        if action == WarmupAction.reply:
            metadata = _fetch_original_message_metadata(client, folder_name, uid)

            to_email = metadata["from_email"]
            subject = metadata["subject"] or "No subject"
            message_id = metadata["message_id"]
            references = metadata["references"]

            if not to_email:
                raise HTTPException(status_code=400, detail="Original sender email not found")
            if not message_id:
                raise HTTPException(status_code=400, detail="Original message-id not found for threading")

            _send_reply_via_smtp(
                mailbox=mailbox,
                to_email=to_email,
                original_subject=subject,
                original_message_id=message_id,
                original_references=references,
                reply_message=reply_message or "",
            )
            return

        raise HTTPException(status_code=400, detail=f"Unsupported IMAP warmup action: {action.value}")
    finally:
        try:
            client.logout()
        except Exception:
            pass