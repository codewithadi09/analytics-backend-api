"""
SQLite connection for the application's OWN operational data (user
accounts, credentials) -- completely separate from
app/database/connection.py, which is the Postgres connection to
rudder_schema (RudderStack's read-only analytics data).

Never mix these two. This module knows nothing about analytics
domains; the Postgres module knows nothing about user accounts.

Uses a single shared aiosqlite connection (not a pool) with WAL mode
enabled -- SQLite is a local file, single-writer by nature, and WAL
mode lets reads and writes proceed concurrently without the "database
is locked" errors that plague default-mode SQLite under any real
concurrent access.
"""

import logging

import aiosqlite

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_connection: aiosqlite.Connection | None = None

_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    is_superadmin INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
)
"""


async def get_app_db() -> aiosqlite.Connection:
    """
    Returns the shared SQLite connection, opening and initializing it
    (WAL mode + table creation) on first call.
    """
    global _connection

    if _connection is None:
        settings = get_settings()
        _connection = await aiosqlite.connect(settings.SQLITE_DB_PATH)
        await _connection.execute("PRAGMA journal_mode=WAL")
        await _connection.execute(_CREATE_USERS_TABLE)
        await _connection.commit()
        logger.info("SQLite app database initialized at %s", settings.SQLITE_DB_PATH)

    return _connection


async def close_app_db() -> None:
    """Closes the SQLite connection. Called from main.py's shutdown lifecycle."""
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None
        logger.info("SQLite app database closed")