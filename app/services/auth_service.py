"""
Auth business logic.

This layer orchestrates the repository (data lookup) and core
security/jwt primitives (verification, token issuance). Routes
(app/api/auth.py) should never talk to the repository or
core.security directly -- always go through here.
"""

import logging

from app.auth.jwt import issue_access_token
from app.core.config import get_settings
from app.core.security import verify_password
from app.repositories.auth_repository import get_user_by_email
from app.schemas.auth import LoginResponse

logger = logging.getLogger(__name__)

# Used to verify against when a user doesn't exist, so login takes
# roughly the same amount of time either way -- prevents timing-based
# user enumeration (an attacker measuring response time to guess
# which emails are registered).
_DUMMY_HASH = (
    "$2b$12$CwTycUXWue0Thq9StjUM0uJ8IvY6XZBqm/L.gr9J3M0hfMz2Q4b5G"
)


class InvalidCredentialsError(Exception):
    """Raised when email/password don't match -- maps to 401 in the route."""


class InactiveUserError(Exception):
    """Raised when credentials are correct but the account is disabled."""


async def login(email: str, password: str) -> LoginResponse:
    """
    Authenticates a user and issues an access token.

    Raises InvalidCredentialsError or InactiveUserError on failure --
    both should map to the same generic 401 at the API layer, so a
    caller can't tell "wrong password" apart from "account disabled"
    or "no such user".
    """
    normalized_email = email.lower().strip()
    user = await get_user_by_email(normalized_email)

    if user is None:
        # Still run a bcrypt verify against a dummy hash so the
        # timing looks the same as a real user with a wrong password.
        verify_password(password, _DUMMY_HASH)
        logger.info("Login attempt for unknown email")
        raise InvalidCredentialsError("Invalid email or password")

    if not verify_password(password, user.hashed_password):
        logger.info("Login attempt with wrong password for user_id=%s", user.user_id)
        raise InvalidCredentialsError("Invalid email or password")

    if not user.is_active:
        logger.info("Login attempt for inactive user_id=%s", user.user_id)
        raise InactiveUserError("Account is disabled")

    token, _jti = await issue_access_token(user.email)
    settings = get_settings()

    logger.info("Successful login for user_id=%s", user.user_id)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )