"""
Async SQLAlchemy engine + session management.

The whole app uses the async ORM path -- no blocking DB calls anywhere,
per the engineering standard of async-only DB access.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Hosted Postgres providers (Supabase, Neon, etc.) enforce TLS on external
# connections. asyncpg needs this passed explicitly via connect_args rather
# than as a `?sslmode=` query param (that's a libpq/psycopg convention, not
# an asyncpg one) -- so DB_SSL_REQUIRE is a dedicated setting rather than
# something embedded in DATABASE_URL. Leave False for local/Docker Postgres.
connect_args = {"ssl": True} if settings.DB_SSL_REQUIRE else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
