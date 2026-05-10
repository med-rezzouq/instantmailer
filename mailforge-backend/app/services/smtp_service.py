import asyncio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


async def send_email(config, to_email: str, subject: str, html_body: str, plain_body: str = "") -> dict:
    def _send():
        print("========== SMTP SEND DEBUG START ==========")
        print("config.host =", config.host)
        print("config.port =", config.port)
        print("config.username =", config.username)
        print("config.from_email =", config.from_email)
        print("config.from_name =", config.from_name)
        print("config.use_ssl =", config.use_ssl)
        print("config.use_tls =", config.use_tls)
        print("to_email =", to_email)
        print("subject =", subject)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{config.from_name or ''} <{config.from_email or config.username}>".strip()
        msg["To"] = to_email

        if plain_body:
            msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        print("SMTP HOST USED =", repr(config.host))
        print("SMTP PORT USED =", repr(config.port))
        print("SMTP USER USED =", repr(config.username))
        print("SMTP SSL USED =", repr(config.use_ssl))
        print("SMTP TLS USED =", repr(config.use_tls))

        try:
            if config.use_ssl:
                print("Connecting with SMTP_SSL...")
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(config.host, config.port, context=ctx, timeout=30) as server:
                    server.set_debuglevel(2)
                    print("SMTP_SSL connected")
                    server.login(config.username, config.password)
                    print("SMTP_SSL login successful")
                    server.sendmail(config.from_email or config.username, to_email, msg.as_string())
                    print("SMTP_SSL sendmail successful")
            else:
                print("Connecting with SMTP...")
                with smtplib.SMTP(config.host, config.port, timeout=30) as server:
                    server.set_debuglevel(2)
                    server.ehlo()
                    print("SMTP connected")

                    if config.use_tls:
                        print("Starting TLS...")
                        ctx = ssl.create_default_context()
                        server.starttls(context=ctx)
                        server.ehlo()
                        print("STARTTLS successful")

                    server.login(config.username, config.password)
                    print("SMTP login successful")

                    server.sendmail(config.from_email or config.username, to_email, msg.as_string())
                    print("SMTP sendmail successful")

            print("========== SMTP SEND DEBUG END ==========")
            return {"status": "sent", "to": to_email}

        except Exception as e:
            print("========== SMTP SEND DEBUG ERROR ==========")
            print(f"SMTP error for {to_email}: {e}")
            print("========== SMTP SEND DEBUG ERROR END ==========")
            raise

    return await asyncio.to_thread(_send)


async def test_connection(config) -> dict:
    def _test():
        print("========== SMTP TEST DEBUG START ==========")
        print("config.host =", config.host)
        print("config.port =", config.port)
        print("config.username =", config.username)
        print("config.use_ssl =", config.use_ssl)
        print("config.use_tls =", config.use_tls)

        try:
            if config.use_ssl:
                print("Testing SMTP_SSL connection...")
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(config.host, config.port, context=ctx, timeout=30) as server:
                    server.set_debuglevel(2)
                    server.login(config.username, config.password)
                    print("SMTP_SSL login successful")
            else:
                print("Testing SMTP connection...")
                with smtplib.SMTP(config.host, config.port, timeout=30) as server:
                    server.set_debuglevel(2)
                    server.ehlo()

                    if config.use_tls:
                        print("Testing STARTTLS...")
                        ctx = ssl.create_default_context()
                        server.starttls(context=ctx)
                        server.ehlo()
                        print("STARTTLS successful")

                    server.login(config.username, config.password)
                    print("SMTP login successful")

            print("========== SMTP TEST DEBUG END ==========")
            return {"status": "ok"}

        except Exception as e:
            print("========== SMTP TEST DEBUG ERROR ==========")
            print(f"SMTP test error: {e}")
            print("========== SMTP TEST DEBUG ERROR END ==========")
            raise

    return await asyncio.to_thread(_test)