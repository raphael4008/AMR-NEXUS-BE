from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from src.core.config import settings

# ── Async Engine ───────────────────────────────────────────────────────────────
# Uses postgresql+asyncpg:// driver for fully non-blocking I/O.
engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
)

# ── Session Factory ────────────────────────────────────────────────────────────
# SQLAlchemy 2.0 canonical API: async_sessionmaker (replaces sessionmaker+class_=AsyncSession).
# expire_on_commit=False prevents implicit lazy-loads after commit in async context.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


# ── FastAPI Dependency ─────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a SQLAlchemy AsyncSession for use as a FastAPI dependency.
    Automatically commits on success and rolls back on any exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise