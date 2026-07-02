"""
Async SQLAlchemy engine + session management.

The whole app uses the async ORM path -- no blocking DB calls anywhere,
per the engineering standard of async-only DB access.
"""

import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


def get_connect_args() -> dict:
    """
    Hosted Postgres poolers (Supabase's Supavisor, Neon, etc.) enforce TLS
    on external connections. asyncpg needs this passed explicitly via
    connect_args rather than a `?sslmode=` query param (that's a
    libpq/psycopg convention, not an asyncpg one).

    Passing ssl=True makes asyncpg do FULL certificate chain verification
    against the system trust store, which fails against Supabase's pooler
    with "self-signed certificate in certificate chain" -- the pooler's
    cert chain isn't fully validate-able against Python's default CA
    bundle. The fix is to still encrypt the connection but skip strict
    chain verification, equivalent to Postgres's sslmode=require (as
    opposed to sslmode=verify-full). This is standard practice for
    connecting through Supavisor/PgBouncer-style poolers.

    Used by both the app's own engine below and by alembic/env.py, so the
    migration engine and the runtime engine behave identically.
    """
    if not settings.DB_SSL_REQUIRE:
        return {}

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return {"ssl": ctx}


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=get_connect_args(),
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