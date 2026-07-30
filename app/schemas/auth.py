"""
Request/response schemas for authentication endpoints.

Username-based, not email-based -- this is an internal tool with no
self-signup; accounts are created only by a superadmin (see
app/schemas/admin.py), so there's no email to verify or send
password-reset links to.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Body of POST /auth/login."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Body returned by POST /auth/login on success."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class RefreshRequest(BaseModel):
    """Body of POST /auth/refresh."""

    refresh_token: str = Field(..., min_length=1, max_length=512)


class RefreshResponse(BaseModel):
    """
    Body returned by POST /auth/refresh -- a new access token AND a
    new refresh token (rotation: the old refresh token is invalidated
    the moment this one is issued).
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class ChangePasswordRequest(BaseModel):
    """
    Body of PATCH /auth/me/password -- any logged-in user (including
    superadmin) changing their OWN password. Requires the current
    password to confirm it's really them, not just someone with a
    still-valid access token sitting at an unlocked computer.
    """

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordResponse(BaseModel):
    """Body returned by PATCH /auth/me/password on success."""

    message: str


class CurrentUser(BaseModel):
    """
    Represents the authenticated user resolved from a valid JWT.
    user_id is the real SQLite integer id, not a string -- used
    directly by admin operations (e.g. resetting a specific member's
    password) without a further lookup.
    """

    username: str
    user_id: int
    is_superadmin: bool