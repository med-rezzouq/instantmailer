import smtplib
import ssl
import email as email_lib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import uuid
from typing import Optional
from app.config import get_settings

settings = get_settings()

def build_reply_to(campaign_id: int, contact_id: int, step_id: int) -> str:
    return f"reply+{campaign_id}+{contact_id}+{step_id}@{settings.REPLY_CATCH_ALL_DOMAIN}"

def build_tracking_pixel(campaign_id: int, contact_id: int, step_id: int) -> str:
    token = f"{campaign_id}-{contact_id}-{step_id}"
    return f'<img src="{settings.TRACKING_BASE_URL}/track/open/{token}" width="1" height="1" style="display:none" />'

def wrap_tracked_links(html: str, campaign_id: int, contact_id: int, step_id: int) -> str:
    import re
    def replace_link(match):
        original_url = match.group(1)
        if settings.TRACKING_BASE_URL in original_url:
            return match.group(0)
        import urllib.parse
        encoded = urllib.parse.quote(original_url, safe='')
        tracked = f"{settings.TRACKING_BASE_URL}/track/click/{campaign_id}/{contact_id}/{step_id}?url={encoded}"
        return f'href="{tracked}"'
    return re.sub(r'href="([^"]+)"', replace_link, html)

def render_template(html: str, contact: dict) -> str:
    for key, value in contact.items():
        html = html.replace(f"{{{{{key}}}}}", str(value or ""))
    return html

async def send_via_smtp(
    smtp_config,
    to_email: str,
    subject: str,
    html_body: str,
    plain_body: str,
    reply_to: str,
    message_id: str,
    campaign_id: int,
    contact_id: int,
    step_id: int,
    attachments: list = []
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"]    = subject
        msg["From"]       = f"{smtp_config.from_name or ''} <{smtp_config.from_email or smtp_config.username}>"
        msg["To"]         = to_email
        msg["Reply-To"]   = reply_to
        msg["Message-ID"] = f"<{message_id}@{settings.REPLY_CATCH_ALL_DOMAIN}>"
        msg["X-Campaign-ID"] = str(campaign_id)
        msg["X-Contact-ID"]  = str(contact_id)
        msg["X-Step-ID"]     = str(step_id)

        pixel  = build_tracking_pixel(campaign_id, contact_id, step_id)
        html_final = wrap_tracked_links(html_body, campaign_id, contact_id, step_id) + pixel

        msg.attach(MIMEText(plain_body or "", "plain"))
        msg.attach(MIMEText(html_final, "html"))

        for att in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(att["content"])
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{att["filename"]}"')
            msg.attach(part)

        if smtp_config.use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_config.host, smtp_config.port, context=ctx, timeout=30) as s:
                s.login(smtp_config.username, smtp_config.password)
                s.sendmail(smtp_config.username, to_email, msg.as_string())
        else:
            with smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=30) as s:
                if smtp_config.use_tls:
                    s.starttls()
                s.login(smtp_config.username, smtp_config.password)
                s.sendmail(smtp_config.username, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"SMTP send error to {to_email}: {e}")
        return False