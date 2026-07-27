"""
Auth repository -- currently backed by an in-memory mock user store.

This is intentionally the ONLY file that will need to change once
real PostgreSQL credentials are available (Phase 12). The function
signatures below are the contract the service layer depends on --
keep them stable when swapping in real SQL.
"""

from dataclasses import dataclass

from app.core.security import hash_password


@dataclass(frozen=True)
class UserRecord:
    """Represents a row from the (future) users table."""

    user_id: str
    email: str
    hashed_password: str
    is_active: bool = True


# ---------------------------------------------------------------------
# MOCK DATA -- replace this whole block with a real SQL query in
# Phase 12. Password for this test user is: "testpassword123"
# ---------------------------------------------------------------------

_MOCK_USERS: dict[str, UserRecord] = {
    "test@example.com": UserRecord(
        user_id="1",
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
    ),
}


async def get_user_by_email(email: str) -> UserRecord | None:
    """
    Looks up a user by email.

    Phase 12 replacement will be an async SQL query, e.g.:
        SELECT id, email, hashed_password, is_active
        FROM users WHERE email = %s
    Signature and return type stay identical -- callers won't change.
    """
    return _MOCK_USERS.get(email.lower())