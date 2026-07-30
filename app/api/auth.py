"""
Authentication routes -- the public endpoints in the API.

Everything else in the application requires a valid bearer token
(see app/auth/dependencies.py). Rate limiting here is Redis-backed
so it survives across multiple app instances/workers, not just a
single process's memory.
"""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.core.constants import RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignupRequest,
    SignupResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InvalidResetTokenError,
    InvalidVerificationTokenError,
    UnverifiedEmailError,
    forgot_password,
    login,
    refresh,
    reset_password,
    signup,
    verify_email,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

_GENERIC_AUTH_ERROR = {
    "message": "Invalid email or password",
    "code": "INVALID_CREDENTIALS",
}

_UNVERIFIED_ERROR = {
    "message": "Please verify your email before logging in",
    "code": "EMAIL_NOT_VERIFIED",
}

_INVALID_REFRESH_ERROR = {
    "message": "Invalid or expired refresh token",
    "code": "INVALID_REFRESH_TOKEN",
}


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
        return await login(payload.email, payload.password)
    except UnverifiedEmailError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_UNVERIFIED_ERROR)
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


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup_route(payload: SignupRequest, request: Request) -> SignupResponse:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_rate_limit("signup", client_ip, settings.LOGIN_RATE_LIMIT_PER_MINUTE)

    try:
        return await signup(payload.email, payload.password)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "An account with this email already exists",
                "code": "EMAIL_ALREADY_REGISTERED",
            },
        )


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email_route(payload: VerifyEmailRequest, request: Request) -> VerifyEmailResponse:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_rate_limit("verify-email", client_ip, settings.LOGIN_RATE_LIMIT_PER_MINUTE)

    try:
        return await verify_email(payload.token)
    except InvalidVerificationTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid or expired verification link",
                "code": "INVALID_VERIFICATION_TOKEN",
            },
        )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password_route(
    payload: ForgotPasswordRequest, request: Request
) -> ForgotPasswordResponse:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_rate_limit("forgot-password", client_ip, settings.LOGIN_RATE_LIMIT_PER_MINUTE)
    return await forgot_password(payload.email)


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password_route(
    payload: ResetPasswordRequest, request: Request
) -> ResetPasswordResponse:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_rate_limit("reset-password", client_ip, settings.LOGIN_RATE_LIMIT_PER_MINUTE)

    try:
        return await reset_password(payload.token, payload.new_password)
    except InvalidResetTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid or expired password reset link",
                "code": "INVALID_RESET_TOKEN",
            },
        )