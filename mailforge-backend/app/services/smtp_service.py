import asyncio, smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

async def send_email(config, to_email: str, subject: str, html_body: str, plain_body: str = "") -> dict:
    def _send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{config.from_name or ''} <{config.from_email or config.username}>".strip()
        msg["To"] = to_email
        if plain_body:
            msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        if config.use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(config.host, config.port, context=ctx) as server:
                server.login(config.username, config.password)
                server.sendmail(config.from_email or config.username, to_email, msg.as_string())
        else:
            with smtplib.SMTP(config.host, config.port) as server:
                if config.use_tls:
                    server.starttls()
                server.login(config.username, config.password)
                server.sendmail(config.from_email or config.username, to_email, msg.as_string())

        return {"status": "sent", "to": to_email}

    return await asyncio.to_thread(_send)

async def test_connection(config) -> dict:
    """Test SMTP credentials without sending an email."""
    def _test():
        if config.use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(config.host, config.port, context=ctx) as server:
                server.login(config.username, config.password)
        else:
            with smtplib.SMTP(config.host, config.port, timeout=10) as server:
                if config.use_tls:
                    server.starttls()
                server.login(config.username, config.password)
        return {"status": "ok"}

    return await asyncio.to_thread(_test)
