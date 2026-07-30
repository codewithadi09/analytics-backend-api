"""
Auth business logic.

This layer orchestrates the repository (data lookup) and core
security/jwt primitives (verification, token issuance). Routes
(app/api/auth.py) should never talk to the repository or
core.security directly -- always go through here.
"""

import logging
import secrets

from app.auth.jwt import issue_access_token
from app.core.config import get_settings
from app.core.constants import (
    EMAIL_VERIFICATION_TTL_SECONDS,
    PASSWORD_RESET_TTL_SECONDS,
    RedisKeyPrefix,
    build_redis_key,
)
from app.core.redis_client import get_redis
from app.core.security import verify_password
from app.repositories.auth_repository import (
    create_user,
    email_exists,
    get_user_by_email,
    mark_user_verified,
    update_user_password,
)
from app.schemas.auth import (
    ForgotPasswordResponse,
    LoginResponse,
    ResetPasswordResponse,
    SignupResponse,
    VerifyEmailResponse,
)

logger = logging.getLogger(__name__)

_DUMMY_HASH = (
    "$2b$12$CwTycUXWue0Thq9StjUM0uJ8IvY6XZBqm/L.gr9J3M0hfMz2Q4b5G"
)


class InvalidCredentialsError(Exception):
    """Raised when email/password don't match -- maps to 401 in the route."""


class InactiveUserError(Exception):
    """Raised when credentials are correct but the account is disabled."""


class UnverifiedEmailError(Exception):
    """Raised when credentials are correct but the email hasn't been verified yet."""


class EmailAlreadyRegisteredError(Exception):
    """Raised on signup if the email is already taken -- maps to 409 in the route."""


class InvalidVerificationTokenError(Exception):
    """Raised when a verification token is missing, expired, or already used."""


class InvalidResetTokenError(Exception):
    """Raised when a password reset token is missing, expired, or already used."""


async def login(email: str, password: str) -> LoginResponse:
    normalized_email = email.lower().strip()
    user = await get_user_by_email(normalized_email)

    if user is None:
        verify_password(password, _DUMMY_HASH)
        logger.info("Login attempt for unknown email")
        raise InvalidCredentialsError("Invalid email or password")

    if not verify_password(password, user.hashed_password):
        logger.info("Login attempt with wrong password for user_id=%s", user.user_id)
        raise InvalidCredentialsError("Invalid email or password")

    if not user.is_active:
        logger.info("Login attempt for inactive user_id=%s", user.user_id)
        raise InactiveUserError("Account is disabled")

    if not user.is_verified:
        logger.info("Login attempt for unverified user_id=%s", user.user_id)
        raise UnverifiedEmailError("Email not verified")

    token, _jti = await issue_access_token(user.email)
    settings = get_settings()

    logger.info("Successful login for user_id=%s", user.user_id)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


async def _send_verification_email(email: str, token: str) -> None:
    """Placeholder for real email delivery -- prints a dev link instead."""
    verification_link = f"http://localhost:3000/verify-email?token={token}"
    logger.info("Verification link for %s: %s", email, verification_link)
    print(f"\n[DEV] Verification link for {email}:\n{verification_link}\n")


async def signup(email: str, password: str) -> SignupResponse:
    normalized_email = email.lower().strip()

    if await email_exists(normalized_email):
        logger.info("Signup attempt for already-registered email")
        raise EmailAlreadyRegisteredError("An account with this email already exists")

    user = await create_user(normalized_email, password)

    token = secrets.token_urlsafe(32)
    redis = await get_redis()
    key = build_redis_key(RedisKeyPrefix.EMAIL_VERIFICATION, token)
    await redis.set(key, user.email, ex=EMAIL_VERIFICATION_TTL_SECONDS)

    await _send_verification_email(user.email, token)

    logger.info("New signup pending verification: user_id=%s", user.user_id)
    return SignupResponse(
        message="Account created. Check your email to verify your account.",
        email=user.email,
    )


async def verify_email(token: str) -> VerifyEmailResponse:
    """
    Consumes a verification token: looks it up in Redis, marks the
    matching account verified, and deletes the token so it can't be
    reused. Raises InvalidVerificationTokenError for a missing,
    expired, or already-used token -- maps to 400 in the route.
    """
    redis = await get_redis()
    key = build_redis_key(RedisKeyPrefix.EMAIL_VERIFICATION, token)

    email = await redis.get(key)
    if email is None:
        logger.info("Invalid or expired verification token presented")
        raise InvalidVerificationTokenError("Invalid or expired verification link")

    await mark_user_verified(email)
    await redis.delete(key)

    logger.info("Email verified: %s", email)
    return VerifyEmailResponse(
        message="Email verified successfully. You can now log in.",
        email=email,
    )


async def _send_password_reset_email(email: str, token: str) -> None:
    """Placeholder for real email delivery -- prints a dev link instead."""
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    logger.info("Password reset link for %s: %s", email, reset_link)
    print(f"\n[DEV] Password reset link for {email}:\n{reset_link}\n")


async def forgot_password(email: str) -> ForgotPasswordResponse:
    """
    ALWAYS returns the same generic response, regardless of whether
    the email is registered -- prevents this endpoint being used to
    enumerate valid accounts, same principle as login()'s dummy
    bcrypt verify against unknown emails.
    """
    normalized_email = email.lower().strip()
    user = await get_user_by_email(normalized_email)

    if user is not None:
        token = secrets.token_urlsafe(32)
        redis = await get_redis()
        key = build_redis_key(RedisKeyPrefix.PASSWORD_RESET, token)
        await redis.set(key, user.email, ex=PASSWORD_RESET_TTL_SECONDS)
        await _send_password_reset_email(user.email, token)
        logger.info("Password reset requested for user_id=%s", user.user_id)
    else:
        logger.info("Password reset requested for unknown email")

    return ForgotPasswordResponse(
        message="If an account exists for this email, a password reset link has been sent."
    )


async def reset_password(token: str, new_password: str) -> ResetPasswordResponse:
    """
    Consumes a password reset token: looks it up in Redis, updates
    the matching account's password, and deletes the token so it
    can't be reused. Raises InvalidResetTokenError for a missing,
    expired, or already-used token -- maps to 400 in the route.
    """
    redis = await get_redis()
    key = build_redis_key(RedisKeyPrefix.PASSWORD_RESET, token)

    email = await redis.get(key)
    if email is None:
        logger.info("Invalid or expired password reset token presented")
        raise InvalidResetTokenError("Invalid or expired password reset link")

    await update_user_password(email, new_password)
    await redis.delete(key)

    logger.info("Password reset completed: %s", email)
    return ResetPasswordResponse(
        message="Password reset successfully. You can now log in with your new password."
    )