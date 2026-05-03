import base64
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import get_settings

settings = get_settings()

AUTH_URI  = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPES    = "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.email"

def get_auth_url(state: str) -> str:
    params = {
        "client_id":     settings.GOOGLE_CLIENT_ID,
        "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPES,
        "access_type":   "offline",
        "prompt":        "consent",
        "state":         state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{AUTH_URI}?{query}"

async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(TOKEN_URI, data={
            "code":          code,
            "client_id":     settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        })
        resp.raise_for_status()
        return resp.json()

async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(TOKEN_URI, data={
            "refresh_token": refresh_token,
            "client_id":     settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type":    "refresh_token",
        })
        resp.raise_for_status()
        return resp.json()

async def send_email(access_token: str, to_email: str, subject: str,
                     html_body: str, plain_body: str = "") -> dict:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["To"] = to_email
    if plain_body:
        msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
        )
        resp.raise_for_status()
    return {"status": "sent", "to": to_email}
