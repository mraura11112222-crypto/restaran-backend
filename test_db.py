import asyncio
import asyncpg

async def check_tables():
    conn = await asyncpg.connect(
        "postgresql://neondb_owner:npg_2VhJWK1GkmLb@ep-round-unit-ad3fdjaq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
    )
    print(f"Tables in Neon ({len(tables)}):")
    for t in tables:
        print(f"  - {t['tablename']}")
    await conn.close()

asyncio.run(check_tables())
