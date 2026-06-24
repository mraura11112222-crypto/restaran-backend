"""Create all tables in Neon database."""
import asyncio
from app.database import engine, Base

# Import all models to register them with Base.metadata
from app.models import *  # noqa

async def create_tables():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done! Checking tables...")
    
    print("Done! All tables created in the database defined by DATABASE_URL.")

asyncio.run(create_tables())
