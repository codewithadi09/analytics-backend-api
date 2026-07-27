"""
JWT issuance and verification at the application level.

Wraps app.core.security's pure encode/decode primitives and adds
Redis-backed revocation (logout support) -- a token can have a
valid signature and not be expired, yet still be rejected because
it was explicitly revoked.
"""

import logging

from jose import JWTError

from app.core.constants import RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.core.security import TokenPayload, create_access_token, decode_access_token

logger = logging.getLogger(__name__)


class TokenRevokedError(Exception):
    """Raised when a token is structurally valid but has been revoked (logged out)."""


async def issue_access_token(subject: str) -> tuple[str, str]:
    """
    Issues a new access token for the given subject (typically the
    user's email or user id). Returns (token, jti).
    """
    return create_access_token(subject)


async def verify_access_token(token: str) -> TokenPayload:
    """
    Verifies a token's signature/expiry AND checks it hasn't been
    revoked. Raises jose.JWTError for invalid/expired tokens, and
    TokenRevokedError for tokens that were explicitly logged out.

    Callers (auth/dependencies.py) translate both into a 401.
    """
    payload = decode_access_token(token)  # raises JWTError if invalid/expired

    redis = await get_redis()
    blacklist_key = build_redis_key(RedisKeyPrefix.JWT_BLACKLIST, payload.jti)
    is_revoked = await redis.exists(blacklist_key)

    if is_revoked:
        raise TokenRevokedError(f"Token {payload.jti} has been revoked")

    return payload


async def revoke_token(jti: str, exp: int) -> None:
    """
    Revokes a token by its jti (called on logout).

    Stored in Redis with a TTL matching the token's remaining
    lifetime -- once the token would have expired naturally anyway,
    there's no need to keep the blacklist entry around, so Redis
    cleans it up for us automatically.
    """
    import time

    redis = await get_redis()
    blacklist_key = build_redis_key(RedisKeyPrefix.JWT_BLACKLIST, jti)
    ttl_seconds = max(exp - int(time.time()), 1)  # at least 1s to avoid a 0/negative TTL
    await redis.set(blacklist_key, "1", ex=ttl_seconds)
    logger.info("Token %s revoked (ttl=%ss)", jti, ttl_seconds)