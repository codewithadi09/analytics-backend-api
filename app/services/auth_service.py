"""
Auth business logic.

Username-based login against the real SQLite user store (see
app/repositories/user_repository.py) -- no more email, no signup, no
verification. Refresh token rotation and password-reset-invalidation
carry forward unchanged from the previous design; only identity
resolution (username vs email) and the user store (SQLite vs
in-memory dict) actually changed.
"""

import logging
import secrets

from app.auth.jwt import issue_access_token
from app.core.config import get_settings
from app.core.constants import REFRESH_TOKEN_TTL_SECONDS, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.core.security import verify_password
from app.repositories.user_repository import (
    get_user_by_id,
    get_user_by_username,
    update_user_password,
)
from app.schemas.auth import ChangePasswordResponse, LoginResponse, RefreshResponse

logger = logging.getLogger(__name__)

_DUMMY_HASH = (
    "$2b$12$CwTycUXWue0Thq9StjUM0uJ8IvY6XZBqm/L.gr9J3M0hfMz2Q4b5G"
)


class InvalidCredentialsError(Exception):
    """Raised when username/password don't match -- maps to 401 in the route."""


class InactiveUserError(Exception):
    """Raised when credentials are correct but the account is disabled."""


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token is missing, expired, already rotated out, or revoked."""


class IncorrectCurrentPasswordError(Exception):
    """Raised when a change-password request's current_password doesn't match."""


async def _issue_refresh_token(user_id: int) -> str:
    """One active refresh token per user -- issuing a new one always
    invalidates whatever existed before, via the user->token index."""
    redis = await get_redis()
    user_index_key = build_redis_key(RedisKeyPrefix.REFRESH_TOKEN_BY_USER, str(user_id))

    old_token = await redis.get(user_index_key)
    if old_token is not None:
        await redis.delete(build_redis_key(RedisKeyPrefix.REFRESH_TOKEN, old_token))

    new_token = secrets.token_urlsafe(32)
    token_key = build_redis_key(RedisKeyPrefix.REFRESH_TOKEN, new_token)

    await redis.set(token_key, str(user_id), ex=REFRESH_TOKEN_TTL_SECONDS)
    await redis.set(user_index_key, new_token, ex=REFRESH_TOKEN_TTL_SECONDS)

    return new_token


async def _revoke_refresh_token_for_user(user_id: int) -> None:
    """Kills a user's current refresh token immediately -- used on password change."""
    redis = await get_redis()
    user_index_key = build_redis_key(RedisKeyPrefix.REFRESH_TOKEN_BY_USER, str(user_id))

    token = await redis.get(user_index_key)
    if token is not None:
        await redis.delete(build_redis_key(RedisKeyPrefix.REFRESH_TOKEN, token))
        await redis.delete(user_index_key)


async def login(username: str, password: str) -> LoginResponse:
    normalized_username = username.lower().strip()
    user = await get_user_by_username(normalized_username)

    if user is None:
        verify_password(password, _DUMMY_HASH)  # timing-attack mitigation, same as before
        logger.info("Login attempt for unknown username")
        raise InvalidCredentialsError("Invalid username or password")

    if not verify_password(password, user.hashed_password):
        logger.info("Login attempt with wrong password for user_id=%s", user.id)
        raise InvalidCredentialsError("Invalid username or password")

    if not user.is_active:
        logger.info("Login attempt for inactive user_id=%s", user.id)
        raise InactiveUserError("Account is disabled")

    access_token, _jti = await issue_access_token(user.username, user.id, user.is_superadmin)
    refresh_token = await _issue_refresh_token(user.id)
    settings = get_settings()

    logger.info("Successful login for user_id=%s", user.id)
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


async def refresh(refresh_token: str) -> RefreshResponse:
    """Trades a valid refresh token for a fresh access token, with rotation."""
    redis = await get_redis()
    token_key = build_redis_key(RedisKeyPrefix.REFRESH_TOKEN, refresh_token)

    user_id_str = await redis.get(token_key)
    if user_id_str is None:
        logger.info("Invalid or expired refresh token presented")
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    user = await get_user_by_id(int(user_id_str))
    if user is None or not user.is_active:
        logger.info("Refresh attempt for inactive/missing user_id=%s", user_id_str)
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    new_access_token, _jti = await issue_access_token(user.username, user.id, user.is_superadmin)
    new_refresh_token = await _issue_refresh_token(user.id)
    settings = get_settings()

    logger.info("Access token refreshed for user_id=%s", user.id)
    return RefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


async def change_own_password(
    user_id: int, current_password: str, new_password: str
) -> ChangePasswordResponse:
    """
    Any logged-in user changing their OWN password -- requires
    confirming the current password first, since a valid access
    token alone (e.g. an unlocked, unattended browser tab) shouldn't
    be sufficient to take over the account permanently.
    """
    user = await get_user_by_id(user_id)
    if user is None:
        # Shouldn't happen -- a valid JWT implies the user existed at
        # issuance time -- but never trust that blindly.
        raise InvalidCredentialsError("User not found")

    if not verify_password(current_password, user.hashed_password):
        logger.info("Incorrect current_password on change-password for user_id=%s", user_id)
        raise IncorrectCurrentPasswordError("Current password is incorrect")

    await update_user_password(user.username, new_password)
    await _revoke_refresh_token_for_user(user_id)  # force re-login on other sessions

    logger.info("Password changed for user_id=%s", user_id)
    return ChangePasswordResponse(message="Password changed successfully.")