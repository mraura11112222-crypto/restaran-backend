"""
Async database engine and session management for Neon PostgreSQL.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
import re

# Strip sslmode and channel_binding from URL (asyncpg doesn't support them as query params)
_db_url = re.sub(r'[?&](sslmode|channel_binding)=[^&]*', '', settings.DATABASE_URL)
# Ensure URL starts with postgresql+asyncpg://
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine for Neon PostgreSQL
engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    # Neon requires SSL
    connect_args={"ssl": True} if "neon.tech" in settings.DATABASE_URL else {},
)

# Async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an async database session.
    Automatically commits on success and rolls back on error.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (for development only, use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
