"""
Low-level security primitives: password hashing and JWT encode/decode.

This module has no knowledge of users, requests, or FastAPI -- it is
pure cryptographic plumbing. Business logic (login flow, current-user
resolution) lives in app/services/auth_service.py and
app/auth/dependencies.py, which call into these functions.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

# bcrypt's algorithm silently ignores any bytes beyond 72 -- meaning
# two different passwords sharing the same first 72 bytes would both
# verify as correct if we let that happen silently. We reject
# oversized passwords explicitly instead. 72 bytes covers well over
# 72 characters of plain ASCII, which is enough for any real password;
# schemas/auth.py should also cap password length at the API layer.
_MAX_PASSWORD_BYTES = 72


class PasswordTooLongError(ValueError):
    """Raised when a password exceeds bcrypt's 72-byte limit."""


# ---------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password for storage. Never store plaintext."""
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > _MAX_PASSWORD_BYTES:
        raise PasswordTooLongError(
            f"Password exceeds the {_MAX_PASSWORD_BYTES}-byte limit."
        )
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored hash.

    Always returns False on malformed hashes, oversized input, or any
    other verification error rather than raising -- a corrupt/legacy
    hash in the DB should behave like a wrong password, not a 500.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > _MAX_PASSWORD_BYTES:
            return False
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------
# JWT encode / decode
# ---------------------------------------------------------------------

class TokenPayload:
    """Lightweight container for a decoded token's claims we care about."""

    def __init__(self, sub: str, jti: str, exp: int, token_type: str) -> None:
        self.sub = sub            # subject -- user identifier (e.g. email or user id)
        self.jti = jti             # unique token id -- used for blacklisting on logout
        self.exp = exp             # expiry (unix timestamp)
        self.token_type = token_type


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> tuple[str, str]:
    """
    Creates a signed JWT access token.

    Returns (token, jti) -- the jti (JWT ID) is returned separately so
    callers can log it or, on logout, push it to the Redis blacklist
    without having to re-decode the token.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid4())

    payload: dict[str, Any] = {
        "sub": subject,
        "jti": jti,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_access_token(token: str) -> TokenPayload:
    """
    Decodes and verifies a JWT access token's signature and expiry.

    Raises jose.JWTError (or a subclass) on any invalid, tampered,
    or expired token -- callers (auth/dependencies.py) are responsible
    for translating that into a 401 response.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    if payload.get("type") != "access":
        raise JWTError("Invalid token type")

    return TokenPayload(
        sub=payload["sub"],
        jti=payload["jti"],
        exp=payload["exp"],
        token_type=payload["type"],
    )