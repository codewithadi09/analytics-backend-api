"""
Shared async Redis connection pool.

One pool is created lazily on first use and reused by every module
that needs Redis (rate limiting, caching, JWT blacklist). Modules
should import get_redis() — never construct their own Redis client.
"""

import logging

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """
    Returns a shared, lazily-initialized async Redis client backed
    by a connection pool. Safe to call from multiple request
    handlers concurrently — the pool is created once.
    """
    global _redis_client

    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(
            str(settings.REDIS_URL),
            max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
            decode_responses=True,  # get str back, not bytes
        )
        logger.info("Redis client initialized (pool max=%s)", settings.REDIS_POOL_MAX_CONNECTIONS)

    return _redis_client


async def close_redis() -> None:
    """
    Gracefully closes the Redis connection pool. Called from the
    FastAPI app's shutdown event in main.py so connections aren't
    left dangling when the process stops.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis client closed")


async def check_redis_connection() -> bool:
    """
    Health check used by main.py's /health endpoint and by startup
    logging, so a misconfigured REDIS_URL fails loudly and visibly
    rather than only surfacing later as a mysterious 500 on first
    cached request.
    """
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception as exc:
        logger.error("Redis connection check failed: %s", exc)
        return False