"""
Request/response schemas for admin-only user management endpoints.
Superadmin creates members and resets their passwords -- there's no
self-signup and no self-service password recovery in this app.
"""

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    """
    Body of POST /admin/users. is_superadmin is deliberately NOT a
    field here -- superadmins can create ordinary members only
    through this route, never other superadmins.
    """

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class CreateUserResponse(BaseModel):
    """Body returned by POST /admin/users on success."""

    message: str
    username: str


class ResetUserPasswordRequest(BaseModel):
    """Body of PATCH /admin/users/{username}/password."""

    new_password: str = Field(..., min_length=8, max_length=128)


class ResetUserPasswordResponse(BaseModel):
    """Body returned by PATCH /admin/users/{username}/password on success."""

    message: str


class UserSummary(BaseModel):
    """
    One row in the admin user list. hashed_password is deliberately
    NOT a field on this model at all -- not filtered out at
    serialization time, just never given anywhere to leak from.
    """

    id: int
    username: str
    is_superadmin: bool
    is_active: bool
    created_at: str


class UserListResponse(BaseModel):
    """Body returned by GET /admin/users."""

    users: list[UserSummary]