"""
Admin business logic -- user provisioning and password resets.
Everything here requires the caller to already be a superadmin
(enforced by app/auth/dependencies.py's require_admin, at the route
layer, not here -- this module trusts that check already happened).
"""

import logging

from app.repositories.user_repository import (
    create_user,
    get_user_by_username,
    list_all_users,
    update_user_password,
    username_exists,
)
from app.schemas.admin import (
    CreateUserResponse,
    ResetUserPasswordResponse,
    UserListResponse,
    UserSummary,
)

logger = logging.getLogger(__name__)


class UsernameAlreadyExistsError(Exception):
    """Raised when creating a user whose username is already taken -- maps to 409."""


class UserNotFoundError(Exception):
    """Raised when resetting a password for a username that doesn't exist -- maps to 404."""


async def create_member(username: str, password: str) -> CreateUserResponse:
    normalized_username = username.lower().strip()

    if await username_exists(normalized_username):
        logger.info("Admin attempted to create already-existing username")
        raise UsernameAlreadyExistsError(f"Username already exists: {normalized_username}")

    user = await create_user(normalized_username, password, is_superadmin=False)
    logger.info("Member created by admin: user_id=%s username=%s", user.id, user.username)

    return CreateUserResponse(message="User created successfully.", username=user.username)


async def reset_member_password(username: str, new_password: str) -> ResetUserPasswordResponse:
    normalized_username = username.lower().strip()
    user = await get_user_by_username(normalized_username)

    if user is None:
        raise UserNotFoundError(f"No such user: {normalized_username}")

    await update_user_password(normalized_username, new_password)
    logger.info("Password reset by admin for user_id=%s", user.id)

    return ResetUserPasswordResponse(message="Password reset successfully.")


async def list_members() -> UserListResponse:
    users = await list_all_users()
    return UserListResponse(
        users=[
            UserSummary(
                id=u.id,
                username=u.username,
                is_superadmin=u.is_superadmin,
                is_active=u.is_active,
                created_at=u.created_at,
            )
            for u in users
        ]
    )