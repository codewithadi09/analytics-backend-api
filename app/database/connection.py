"""
Async PostgreSQL connection pool.

Deliberately safe to import and use even when DATABASE_URL is not
set -- per the layered-build plan, repositories run on mock data
until real credentials exist (Phase 12). Any repository that tries
to actually acquire a connection before then gets a clear
DatabaseNotConfiguredError instead of a confusing connection
failure or a silent crash at import time.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool | None = None


class DatabaseNotConfiguredError(Exception):
    """Raised when a repository tries to query before DATABASE_URL is set."""


async def get_pool() -> AsyncConnectionPool:
    """
    Returns the shared connection pool, creating it lazily on first
    use. Raises DatabaseNotConfiguredError if DATABASE_URL isn't set --
    this is expected and fine during Phases 4-11, since repositories
    are still mock-backed.
    """
    global _pool

    settings = get_settings()
    if settings.DATABASE_URL is None:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not set. This is expected until Phase 12 -- "
            "repositories should be using mock data, not calling get_pool()."
        )

    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=str(settings.DATABASE_URL),
            min_size=settings.DB_POOL_MIN_SIZE,
            max_size=settings.DB_POOL_MAX_SIZE,
            timeout=settings.DB_CONNECT_TIMEOUT_SECONDS,
            open=False,  # opened explicitly below to control startup ordering
        )
        await _pool.open()
        logger.info(
            "PostgreSQL pool opened (min=%s, max=%s)",
            settings.DB_POOL_MIN_SIZE,
            settings.DB_POOL_MAX_SIZE,
        )

    return _pool


@asynccontextmanager
async def get_connection() -> AsyncIterator[AsyncConnection]:
    """
    Convenience context manager for repositories:

        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT ...")
                rows = await cur.fetchall()

    Connections are returned to the pool automatically on exit,
    including when an exception is raised.
    """
    pool = await get_pool()
    async with pool.connection() as conn:
        yield conn


async def close_pool() -> None:
    """Closes the pool cleanly. Called from main.py's shutdown lifecycle."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL pool closed")


async def check_database_connection() -> bool:
    """
    Health check used by /health. Returns False (not an exception)
    when DATABASE_URL isn't configured yet -- that's a normal,
    expected state during early phases, not an error condition.
    """
    settings = get_settings()
    if settings.DATABASE_URL is None:
        return False

    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        return True
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        return False