"""
Authentication routes -- the one public endpoint in the API.

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
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import (
    InactiveUserError,
    InvalidCredentialsError,
    login,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

_GENERIC_AUTH_ERROR = {
    "message": "Invalid email or password",
    "code": "INVALID_CREDENTIALS",
}


async def _enforce_login_rate_limit(client_ip: str) -> None:
    """
    Fixed-window rate limit keyed by client IP: N attempts per
    60-second window. Simple and effective against brute-force;
    not trying to be a full sliding-window/token-bucket here --
    that's a Phase 11 hardening concern if it proves necessary.
    """
    settings = get_settings()
    redis = await get_redis()
    key = build_redis_key(RedisKeyPrefix.RATE_LIMIT, "login", client_ip)

    current = await redis.incr(key)
    if current == 1:
        # First request in this window -- set the window to expire in 60s.
        await redis.expire(key, 60)

    if current > settings.LOGIN_RATE_LIMIT_PER_MINUTE:
        logger.warning("Login rate limit exceeded for ip=%s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Too many login attempts. Try again shortly.",
                "code": "RATE_LIMITED",
            },
        )


@router.post("/login", response_model=LoginResponse)
async def login_route(payload: LoginRequest, request: Request) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_login_rate_limit(client_ip)

    try:
        return await login(payload.email, payload.password)
    except (InvalidCredentialsError, InactiveUserError):
        # Same status/body for both -- don't leak which failure mode occurred.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_GENERIC_AUTH_ERROR,
        )