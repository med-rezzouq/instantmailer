import asyncio
from app.database import Base, engine
import app.models

async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("DONE")

asyncio.run(create())