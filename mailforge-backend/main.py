from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.database import engine, Base
from app.middleware.rate_limit import limiter
from app.routers import auth, oauth, oauth_apps, contacts, campaigns, templates, analytics, webhooks, smtp, campaign_v2, tracking, powermta, ai, tracking,mailboxes, imapmailboxes,warmup
from app.routers.ai import router as ai_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="InstantMailer API",
    description="Email marketing platform using Microsoft 365, Google Workspace & SMTP",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:80", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(contacts.router)
app.include_router(campaigns.router)
app.include_router(templates.router)
app.include_router(analytics.router)
app.include_router(webhooks.router)
app.include_router(smtp.router)
app.include_router(tracking.router)
app.include_router(campaign_v2.router)
app.include_router(powermta.router)
app.include_router(ai.router)
app.include_router(mailboxes.router)
app.include_router(imapmailboxes.router)
app.include_router(warmup.router)
app.include_router(oauth_apps.router)
app.include_router(ai_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/debug-routes")
async def debug_routes():
    return sorted(
        [
            f"{','.join(route.methods or [])} {route.path}"
            for route in app.routes
        ]
    )