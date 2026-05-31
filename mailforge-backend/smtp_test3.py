import os
import smtplib
import socket
import ssl
import sys
from email.message import EmailMessage
from dotenv import load_dotenv
import uuid

load_dotenv()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def fail(message: str, code: int = 1):
    print(message)
    sys.exit(code)


# Use RELAY_ variables
host = os.getenv("RELAY_SMTP_HOST")
port = int(os.getenv("RELAY_SMTP_PORT", "587"))
username = os.getenv("RELAY_SMTP_USERNAME")
password = os.getenv("RELAY_SMTP_PASSWORD")
from_email = os.getenv("RELAY_SMTP_FROM") or username
to_email = os.getenv("RELAY_SMTP_TO")
use_ssl = env_bool("RELAY_SMTP_SSL", False)
use_starttls = env_bool("RELAY_SMTP_STARTTLS", port == 587)
timeout = int(os.getenv("RELAY_SMTP_TIMEOUT", "15"))

if not host:
    fail("Missing RELAY_SMTP_HOST environment variable")

if use_ssl and use_starttls:
    fail("Use either RELAY_SMTP_SSL=true or RELAY_SMTP_STARTTLS=true, not both")

print(f"Testing RELAY SMTP server {host}:{port}")
print(f"SSL={use_ssl} STARTTLS={use_starttls}")

server = None
try:
    if use_ssl:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
    else:
        server = smtplib.SMTP(host, port, timeout=timeout)

    server.set_debuglevel(1)

    code, banner = server.ehlo()
    print(f"EHLO: {code} {banner.decode(errors='ignore') if isinstance(banner, bytes) else banner}")

    if use_starttls:
        context = ssl.create_default_context()
        code, resp = server.starttls(context=context)
        print(f"STARTTLS: {code} {resp.decode(errors='ignore') if isinstance(resp, bytes) else resp}")
        code, banner = server.ehlo()
        print(f"EHLO after TLS: {code} {banner.decode(errors='ignore') if isinstance(banner, bytes) else banner}")

    if username and password:
        server.login(username, password)
        print("Login successful")
    else:
        print("Skipping login because RELAY_SMTP_USERNAME/RELAY_SMTP_PASSWORD are not set")

    if to_email:
        if not from_email:
            fail("RELAY_SMTP_FROM is required when RELAY_SMTP_TO is set")

        msg = EmailMessage()
        msg["Message-ID"] = f"<{uuid.uuid4()}@academicsights.com>"
        msg["Subject"] = "Hi Mohammed are you interested for a webinar"
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(
            "Whats'up i will contact you about the guide of using the ebook soon again! next week "
        )

        server.send_message(msg)
        print(f"Test email sent to {to_email}")
    else:
        print("Connection test passed. Set RELAY_SMTP_TO to send a real test email.")

except (smtplib.SMTPException, socket.error, ssl.SSLError) as exc:
    fail(f"SMTP test failed: {exc}")
finally:
    if server is not None:
        try:
            server.quit()
        except Exception:
            pass