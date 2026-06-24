import asyncio
from sqlalchemy import text
from app.database import engine

async def fix_db():
    print("Fixing database schema...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
            print("Added is_active to users")
        except Exception as e:
            print("Error is_active:", e)

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);"))
            print("Added avatar_url to users")
        except Exception as e:
            print("Error avatar_url:", e)

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS branch_id UUID;"))
            print("Added branch_id to users")
        except Exception as e:
            print("Error branch_id:", e)
            
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(255);"))
            print("Added username to users")
        except Exception as e:
            print("Error username:", e)

            
        try:
            await conn.execute(text("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SUPER_ADMIN';"))
            print("Added SUPER_ADMIN to user_role")
        except Exception as e:
            print("Error user_role:", e)

    print("Done fixing db!")

asyncio.run(fix_db())
