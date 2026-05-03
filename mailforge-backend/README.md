# MailForge Backend API

FastAPI backend for the MailForge email marketing platform.
Supports **Microsoft 365** (Graph API) and **Google Workspace** (Gmail API) for sending bulk emails.

---

## Stack
- **FastAPI** + **async/await** (Python 3.12)
- **MySQL 8** via SQLAlchemy async (aiomysql)
- **JWT** authentication (python-jose)
- **Docker** + Docker Compose
- **Rate limiting** via SlowAPI

---

## Quick Start

### 1. Clone & Configure
```bash
cp .env.example .env
# Edit .env with your secrets
```

### 2. Register OAuth Apps

#### Microsoft 365
1. Go to https://portal.azure.com → **App registrations** → New registration
2. Set Redirect URI: `http://localhost:8000/oauth/microsoft/callback`
3. Under **API permissions** → Add `Mail.Send` and `User.Read` (Microsoft Graph)
4. Create a **Client secret** under Certificates & secrets
5. Copy `Application (client) ID`, `Client secret`, `Directory (tenant) ID` → paste into `.env`

#### Google Workspace
1. Go to https://console.cloud.google.com → **APIs & Services** → Enable **Gmail API**
2. Go to **OAuth consent screen** → Configure (External or Internal)
3. Go to **Credentials** → Create OAuth 2.0 Client ID (Web application)
4. Set Authorized redirect URI: `http://localhost:8000/oauth/google/callback`
5. Copy `Client ID` and `Client Secret` → paste into `.env`

### 3. Run with Docker
```bash
docker compose up --build
```

API is live at: http://localhost:8000
Interactive docs: http://localhost:8000/docs
DB admin (Adminer): http://localhost:8080

### 4. Run Locally (without Docker)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# make sure MySQL is running and DATABASE_URL is set
uvicorn main:app --reload
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | ❌ | Register new user |
| POST | /auth/login | ❌ | Login, get JWT tokens |
| POST | /auth/refresh | ❌ | Refresh access token |
| GET  | /auth/me | ✅ | Current user profile |
| GET  | /oauth/microsoft/connect | ✅ | Get Microsoft OAuth URL |
| GET  | /oauth/microsoft/callback | ❌ | Microsoft OAuth callback |
| GET  | /oauth/google/connect | ✅ | Get Google OAuth URL |
| GET  | /oauth/google/callback | ❌ | Google OAuth callback |
| GET  | /oauth/status | ✅ | Connected providers |
| GET  | /contacts | ✅ | List contacts |
| POST | /contacts | ✅ | Create contact |
| POST | /contacts/import | ✅ | Bulk import contacts |
| PUT  | /contacts/{id} | ✅ | Update contact |
| DELETE | /contacts/{id} | ✅ | Delete contact |
| GET  | /contacts/tags | ✅ | List tags |
| POST | /contacts/tags | ✅ | Create tag |
| GET  | /campaigns | ✅ | List campaigns |
| POST | /campaigns | ✅ | Create campaign |
| GET  | /campaigns/{id} | ✅ | Get campaign |
| PUT  | /campaigns/{id} | ✅ | Update campaign |
| DELETE | /campaigns/{id} | ✅ | Delete campaign |
| POST | /campaigns/{id}/send | ✅ | **Send campaign** (async bulk) |
| GET  | /templates | ✅ | List templates |
| POST | /templates | ✅ | Create template |
| GET  | /analytics/dashboard | ✅ | Dashboard stats |
| GET  | /analytics/campaigns/{id} | ✅ | Campaign stats |
| POST | /webhooks/delivery | ❌ | Delivery status webhook |
| GET  | /webhooks/track/open/{cid}/{uid} | ❌ | Open tracking pixel |

---

## Personalization Tags
Use these in your campaign HTML content:
- `{{first_name}}` → Recipient's first name
- `{{email}}` → Recipient's email

---

## How Bulk Sending Works
1. POST `/campaigns/{id}/send` triggers a background task
2. All subscribed contacts matching the campaign's segment tags are fetched
3. `asyncio.gather()` fires up to `SEND_CONCURRENCY_LIMIT` (default: 50) simultaneous API requests
4. Each result is handled independently — failures are logged without stopping others
5. Campaign status updates: `draft` → `sending` → `sent`
