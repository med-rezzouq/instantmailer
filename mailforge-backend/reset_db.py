import asyncio
from sqlalchemy import text
from app.database import engine, Base
from app.models import user, contact, template, oauthtoken, smtpconfig, campaign, campaigncontact, campaignevent, campaignrun, campaignsender, campaignstep, powermtareply, analytics

async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        await conn.run_sync(Base.metadata.create_all)
    print("database reset complete")

asyncio.run(main())
