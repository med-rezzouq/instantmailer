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
    import urllib.parse

    def replace_link(match):
        original_url = match.group(1)
        if settings.TRACKING_BASE_URL in original_url:
            return match.group(0)
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
        print("========== SMTP DEBUG START ==========")
        print("to_email =", to_email)
        print("smtp_config.host =", smtp_config.host)
        print("smtp_config.port =", smtp_config.port)
        print("smtp_config.username =", smtp_config.username)
        print("smtp_config.use_ssl =", smtp_config.use_ssl)
        print("smtp_config.use_tls =", smtp_config.use_tls)
        print("smtp_config.from_email =", smtp_config.from_email)
        print("smtp_config.from_name =", smtp_config.from_name)
        print("reply_to =", reply_to)
        print("message_id =", message_id)
        print("campaign_id =", campaign_id)
        print("contact_id =", contact_id)
        print("step_id =", step_id)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{smtp_config.from_name or ''} <{smtp_config.from_email or smtp_config.username}>"
        msg["To"] = to_email
        msg["Reply-To"] = reply_to
        msg["Message-ID"] = f"<{message_id}@{settings.REPLY_CATCH_ALL_DOMAIN}>"
        msg["X-Campaign-ID"] = str(campaign_id)
        msg["X-Contact-ID"] = str(contact_id)
        msg["X-Step-ID"] = str(step_id)

        pixel = build_tracking_pixel(campaign_id, contact_id, step_id)
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
            print("Connecting with SMTP_SSL...")
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_config.host, smtp_config.port, context=ctx, timeout=30) as s:
                s.set_debuglevel(2)
                print("SMTP_SSL connected")
                s.login(smtp_config.username, smtp_config.password)
                print("SMTP_SSL login successful")
                s.sendmail(smtp_config.username, to_email, msg.as_string())
                print("SMTP_SSL sendmail successful")
        else:
            print("Connecting with SMTP...")
            with smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=30) as s:
                s.set_debuglevel(2)
                s.ehlo()
                print("SMTP connected")

                if smtp_config.use_tls:
                    print("Starting TLS...")
                    ctx = ssl.create_default_context()
                    s.starttls(context=ctx)
                    s.ehlo()
                    print("STARTTLS successful")

                s.login(smtp_config.username, smtp_config.password)
                print("SMTP login successful")

                s.sendmail(smtp_config.username, to_email, msg.as_string())
                print("SMTP sendmail successful")

        print("========== SMTP DEBUG END ==========")
        return True

    except Exception as e:
        print("========== SMTP DEBUG ERROR ==========")
        print(f"SMTP send error to {to_email}: {e}")
        print("========== SMTP DEBUG ERROR END ==========")
        return False