"""
Auth repository -- currently backed by an in-memory mock user store.

This will need to become a real database table once you have write
access to create one (a users table, separate from rudder_schema --
that schema belongs to RudderStack's read-only analytics data, not
your application's own accounts). Until then, this in-memory store
lets the full signup/login/verification flow work end-to-end for
development and testing. Restarting the server clears all signed-up
users -- the original test account below is the only one that always
comes back.
"""

from dataclasses import dataclass, replace

from app.core.security import hash_password


@dataclass(frozen=True)
class UserRecord:
    """Represents a row from the (future) users table."""

    user_id: str
    email: str
    hashed_password: str
    role: str = "viewer"
    is_active: bool = True
    is_verified: bool = True


# ---------------------------------------------------------------------
# MOCK DATA -- pre-seeded test account. Password: "testpassword123"
# Given admin role so you can test admin-only endpoints once they exist.
# ---------------------------------------------------------------------

_MOCK_USERS: dict[str, UserRecord] = {
    "test@example.com": UserRecord(
        user_id="1",
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        role="admin",
        is_active=True,
        is_verified=True,
    ),
}

_next_user_id = 2


async def get_user_by_email(email: str) -> UserRecord | None:
    """Looks up a user by email."""
    return _MOCK_USERS.get(email.lower())


async def email_exists(email: str) -> bool:
    """Checks whether an account already exists for this email."""
    return email.lower() in _MOCK_USERS


async def create_user(email: str, plain_password: str) -> UserRecord:
    """
    Creates a new, unverified user with the default 'viewer' role.

    Raises ValueError if the email is already taken -- callers should
    check email_exists() first for a cleaner error message, but this
    guard exists so create_user() is never accidentally unsafe to
    call on its own.
    """
    global _next_user_id

    normalized_email = email.lower()
    if normalized_email in _MOCK_USERS:
        raise ValueError(f"Email already registered: {normalized_email}")

    user = UserRecord(
        user_id=str(_next_user_id),
        email=normalized_email,
        hashed_password=hash_password(plain_password),
        role="viewer",
        is_active=True,
        is_verified=False,
    )
    _MOCK_USERS[normalized_email] = user
    _next_user_id += 1
    return user


async def mark_user_verified(email: str) -> None:
    """Flips is_verified to True after a successful email verification."""
    normalized_email = email.lower()
    existing = _MOCK_USERS.get(normalized_email)
    if existing is not None:
        _MOCK_USERS[normalized_email] = replace(existing, is_verified=True)

async def get_user_by_id(user_id: str) -> UserRecord | None:
    """Looks up a user by their internal id, not email."""
    for user in _MOCK_USERS.values():
        if user.user_id == user_id:
            return user
    return None