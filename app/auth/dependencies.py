"""
FastAPI dependencies for authentication.

Import get_current_user into any route that should require a valid
JWT. Import require_rate_limit alongside it on routes that should
also enforce a general-purpose per-user request limit. Import
require_admin on routes that should additionally be restricted to
superadmin accounts only.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.jwt import TokenRevokedError, verify_access_token
from app.core.constants import RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.schemas.auth import CurrentUser

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=True)

_GENERAL_RATE_LIMIT_PER_MINUTE = 120

_INVALID_TOKEN_ERROR = {"message": "Invalid or expired token", "code": "TOKEN_INVALID"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    Resolves the authenticated user from the request's bearer token.

    Raises 401 for any failure mode (invalid signature, expired,
    revoked, or missing user_id claim) -- deliberately the same
    status/message for all of them, so a caller probing the API
    can't distinguish one failure mode from another.
    """
    token = credentials.credentials

    try:
        payload = await verify_access_token(token)
    except TokenRevokedError:
        logger.info("Rejected revoked token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_TOKEN_ERROR,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        logger.info("Rejected invalid/expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_TOKEN_ERROR,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.user_id is None:
        logger.info("Rejected token with no user_id claim (legacy or malformed)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_TOKEN_ERROR,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        username=payload.sub,
        user_id=payload.user_id,
        is_superadmin=payload.is_superadmin,
    )


async def require_rate_limit(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    General-purpose per-user rate limit, applied on top of
    authentication. Depends on get_current_user so an invalid token
    gets a 401 before ever touching the rate limit counter.
    """
    redis = await get_redis()
    key = build_redis_key(RedisKeyPrefix.RATE_LIMIT, "general", str(current_user.user_id))

    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)

    if current > _GENERAL_RATE_LIMIT_PER_MINUTE:
        logger.warning("General rate limit exceeded for user_id=%s", current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": "Too many requests. Please slow down.", "code": "RATE_LIMITED"},
        )

    return current_user


async def require_admin(current_user: CurrentUser = Depends(require_rate_limit)) -> CurrentUser:
    """
    Restricts a route to superadmin accounts only. Layered on top of
    require_rate_limit (which itself layers on get_current_user), so
    a non-admin caller still gets rate-limited before being told
    they lack permission -- consistent ordering with the rest of the
    dependency chain.
    """
    if not current_user.is_superadmin:
        logger.warning("Non-admin user_id=%s attempted an admin-only route", current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Admin access required", "code": "ADMIN_REQUIRED"},
        )
    return current_user