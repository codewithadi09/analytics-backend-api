"""
Request/response schemas for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Body of POST /login."""

    email: EmailStr
    # Bounded so an absurdly long string can't be sent through to
    # bcrypt before core/security.py's own length check even runs --
    # this keeps a clearly-invalid request from doing any hashing work.
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Body returned by POST /login on success."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int

class CurrentUser(BaseModel):
    """
    Represents the authenticated user resolved from a valid JWT.

    Returned by the auth dependency (Phase 2, next file) and used
    by protected routes that need to know who's calling -- e.g. to
    scope a query or just to return via GET /me.
    """

    email: EmailStr
    user_id: str

class SignupRequest(BaseModel):
    """Body of POST /auth/signup."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class SignupResponse(BaseModel):
    """Body returned by POST /auth/signup -- no token yet, account needs verification first."""

    message: str
    email: EmailStr

class VerifyEmailRequest(BaseModel):
    """Body of POST /auth/verify-email."""

    token: str = Field(..., min_length=1, max_length=256)


class VerifyEmailResponse(BaseModel):
    """Body returned by POST /auth/verify-email on success."""

    message: str
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    """Body of POST /auth/forgot-password."""

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """
    Body returned by POST /auth/forgot-password -- ALWAYS this same
    generic message, whether or not the email is actually registered.
    Prevents using this endpoint to enumerate valid accounts.
    """

    message: str


class ResetPasswordRequest(BaseModel):
    """Body of POST /auth/reset-password."""

    token: str = Field(..., min_length=1, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    """Body returned by POST /auth/reset-password on success."""

    message: str

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