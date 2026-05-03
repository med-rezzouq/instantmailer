import httpx
import msal
from datetime import datetime, timezone
from app.config import get_settings

settings = get_settings()

GRAPH_SEND_URL = "https://graph.microsoft.com/v1.0/me/sendMail"
GRAPH_ME_URL   = "https://graph.microsoft.com/v1.0/me"
SCOPES         = ["Mail.Send", "User.Read"]

def get_auth_url(state: str) -> str:
    app = msal.ConfidentialClientApplication(
        settings.MICROSOFT_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}",
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
    )
    return app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=settings.MICROSOFT_REDIRECT_URI,
        state=state,
    )

async def exchange_code(code: str) -> dict:
    app = msal.ConfidentialClientApplication(
        settings.MICROSOFT_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}",
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
    )
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=settings.MICROSOFT_REDIRECT_URI,
    )
    if "error" in result:
        raise ValueError(result.get("error_description", "Microsoft OAuth failed"))
    return result

async def refresh_access_token(refresh_token: str) -> dict:
    app = msal.ConfidentialClientApplication(
        settings.MICROSOFT_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}",
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
    )
    result = app.acquire_token_by_refresh_token(refresh_token, scopes=SCOPES)
    if "error" in result:
        raise ValueError(result.get("error_description", "Token refresh failed"))
    return result

async def send_email(access_token: str, to_email: str, subject: str, html_body: str,
                     plain_body: str = "", from_name: str = "") -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
        },
        "saveToSentItems": "false",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GRAPH_SEND_URL, headers=headers, json=payload)
        resp.raise_for_status()
    return {"status": "sent", "to": to_email}
