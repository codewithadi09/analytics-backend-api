"""
User account repository -- real SQLite queries against the app's own
users table (see app/database/app_connection.py). Replaces the old
in-memory mock auth_repository.py entirely.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.security import hash_password
from app.database.app_connection import get_app_db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UserRecord:
    """Represents one row from the users table."""

    id: int
    username: str
    hashed_password: str
    is_superadmin: bool
    is_active: bool
    created_at: str


def _row_to_user(row: tuple) -> UserRecord:
    return UserRecord(
        id=row[0],
        username=row[1],
        hashed_password=row[2],
        is_superadmin=bool(row[3]),
        is_active=bool(row[4]),
        created_at=row[5],
    )


async def get_user_by_username(username: str) -> UserRecord | None:
    db = await get_app_db()
    async with db.execute(
        "SELECT id, username, hashed_password, is_superadmin, is_active, created_at "
        "FROM users WHERE username = ?",
        (username.lower(),),
    ) as cursor:
        row = await cursor.fetchone()
        return _row_to_user(row) if row else None


async def get_user_by_id(user_id: int) -> UserRecord | None:
    db = await get_app_db()
    async with db.execute(
        "SELECT id, username, hashed_password, is_superadmin, is_active, created_at "
        "FROM users WHERE id = ?",
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
        return _row_to_user(row) if row else None


async def username_exists(username: str) -> bool:
    return await get_user_by_username(username) is not None


async def create_user(username: str, plain_password: str, is_superadmin: bool = False) -> UserRecord:
    """
    Creates a new user. Raises sqlite3.IntegrityError (via aiosqlite)
    if the username is already taken -- callers should check
    username_exists() first for a cleaner error, but the UNIQUE
    constraint is the real, unbypassable guarantee.
    """
    db = await get_app_db()
    normalized_username = username.lower()
    hashed = hash_password(plain_password)
    created_at = datetime.now(timezone.utc).isoformat()

    cursor = await db.execute(
        "INSERT INTO users (username, hashed_password, is_superadmin, is_active, created_at) "
        "VALUES (?, ?, ?, 1, ?)",
        (normalized_username, hashed, int(is_superadmin), created_at),
    )
    await db.commit()

    user = await get_user_by_id(cursor.lastrowid)
    assert user is not None  # just inserted -- must exist
    return user


async def update_user_password(username: str, new_plain_password: str) -> None:
    db = await get_app_db()
    hashed = hash_password(new_plain_password)
    await db.execute(
        "UPDATE users SET hashed_password = ? WHERE username = ?",
        (hashed, username.lower()),
    )
    await db.commit()


async def list_all_users() -> list[UserRecord]:
    db = await get_app_db()
    async with db.execute(
        "SELECT id, username, hashed_password, is_superadmin, is_active, created_at "
        "FROM users ORDER BY created_at ASC"
    ) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_user(r) for r in rows]


async def seed_superadmin_if_missing(username: str, plain_password: str) -> None:
    """
    Called once at app startup. Creates the bootstrap superadmin
    account if it doesn't already exist -- safe to call on every
    startup, since it checks first and is a no-op thereafter. This is
    what lets the superadmin's password be CHANGED later via
    PATCH /auth/me/password and have that change persist across
    restarts, rather than the account being re-created fresh (and
    the change lost) every time the app boots.
    """
    existing = await get_user_by_username(username)
    if existing is not None:
        return

    await create_user(username, plain_password, is_superadmin=True)
    logger.info("Bootstrap superadmin account created: %s", username)