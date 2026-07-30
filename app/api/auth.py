"""
Authentication routes.

Username-based login only -- no signup, no email verification, no
self-service password reset. Accounts are provisioned exclusively by
a superadmin via the /admin routes (see app/api/admin.py); a
superadmin resets a member's forgotten password directly, rather
than the member self-serving through an emailed link.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.constants import RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    CurrentUser,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.services.auth_service import (
    IncorrectCurrentPasswordError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    change_own_password,
    login,
    refresh,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

_GENERIC_AUTH_ERROR = {"message": "Invalid username or password", "code": "INVALID_CREDENTIALS"}
_INVALID_REFRESH_ERROR = {"message": "Invalid or expired refresh token", "code": "INVALID_REFRESH_TOKEN"}


async def _enforce_rate_limit(action: str, client_ip: str, limit_per_minute: int) -> None:
    redis = await get_redis()
    key = build_redis_key(RedisKeyPrefix.RATE_LIMIT, action, client_ip)

    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)

    if current > limit_per_minute:
        logger.warning("Rate limit exceeded for action=%s ip=%s", action, client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": "Too many attempts. Try again shortly.", "code": "RATE_LIMITED"},
        )


@router.post("/login", response_model=LoginResponse)
async def login_route(payload: LoginRequest, request: Request) -> LoginResponse:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_rate_limit("login", client_ip, settings.LOGIN_RATE_LIMIT_PER_MINUTE)

    try:
        return await login(payload.username, payload.password)
    except (InvalidCredentialsError, InactiveUserError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_GENERIC_AUTH_ERROR)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_route(payload: RefreshRequest, request: Request) -> RefreshResponse:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_rate_limit("refresh", client_ip, settings.LOGIN_RATE_LIMIT_PER_MINUTE)

    try:
        return await refresh(payload.refresh_token)
    except InvalidRefreshTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_REFRESH_ERROR)


@router.patch("/me/password", response_model=ChangePasswordResponse)
async def change_own_password_route(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ChangePasswordResponse:
    try:
        return await change_own_password(
            current_user.user_id, payload.current_password, payload.new_password
        )
    except IncorrectCurrentPasswordError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Current password is incorrect", "code": "INCORRECT_PASSWORD"},
        )