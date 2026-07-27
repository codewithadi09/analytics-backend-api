"""
FastAPI dependencies for authentication.

Import get_current_user into any route that should require a valid
JWT. Import require_rate_limit alongside it on routes that should
also enforce a general-purpose per-user request limit (most routes
already do this implicitly via the Redis cache reducing repeat
load, but this is a hard backstop for cache misses and expensive
uncached endpoints).
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

# General-purpose limit: generous enough that no legitimate dashboard
# usage pattern (multiple charts loading on page open, filters being
# adjusted) hits it, but low enough to stop runaway polling loops or
# scraping. Login has its own stricter, separate limit.
_GENERAL_RATE_LIMIT_PER_MINUTE = 120


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    Resolves the authenticated user from the request's bearer token.

    Raises 401 for any failure mode (invalid signature, expired,
    revoked) -- deliberately the same status/message for all of
    them, so a caller probing the API can't distinguish "expired"
    from "revoked" from "tampered" and infer internal state.
    """
    token = credentials.credentials

    try:
        payload = await verify_access_token(token)
    except TokenRevokedError:
        logger.info("Rejected revoked token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired token", "code": "TOKEN_INVALID"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        logger.info("Rejected invalid/expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired token", "code": "TOKEN_INVALID"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(email=payload.sub, user_id=payload.sub)


async def require_rate_limit(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    General-purpose per-user rate limit, applied on top of
    authentication. Depends on get_current_user so it always runs
    AFTER identity is confirmed -- an invalid token gets a 401
    before ever touching the rate limit counter, so attackers can't
    burn through a legitimate user's quota with garbage tokens.
    """
    redis = await get_redis()
    key = build_redis_key(RedisKeyPrefix.RATE_LIMIT, "general", current_user.user_id)

    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)

    if current > _GENERAL_RATE_LIMIT_PER_MINUTE:
        logger.warning("General rate limit exceeded for user_id=%s", current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Too many requests. Please slow down.",
                "code": "RATE_LIMITED",
            },
        )

    return current_user