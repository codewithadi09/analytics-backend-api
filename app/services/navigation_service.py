"""
Navigation Path Analysis business logic.

Longer cache TTL than Traffic/Interactions -- this is a heavier query
(window functions, per-session grouping) and navigation patterns shift
slowly, same reasoning the old retention_service.py used for the
retention curve.
"""

import asyncio
import logging

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.navigation_repository import (
    get_average_pages_per_session,
    get_exit_rates,
    get_top_navigation_paths,
    get_total_sessions,
)
from app.schemas.navigation import ExitRateByPage, NavigationOverviewResponse, NavigationPath

logger = logging.getLogger(__name__)

_TOP_PATHS_LIMIT = 10


async def get_navigation_overview() -> NavigationOverviewResponse:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "navigation", "overview")
    redis = await get_redis()

    cached = await redis.get(cache_key)
    if cached is not None:
        logger.info("Navigation overview served from cache")
        return NavigationOverviewResponse.model_validate_json(cached)

    total_sessions, path_rows, avg_pages, exit_rate_rows = await asyncio.gather(
        get_total_sessions(),
        get_top_navigation_paths(_TOP_PATHS_LIMIT),
        get_average_pages_per_session(),
        get_exit_rates(),
    )

    top_paths = [
        NavigationPath(
            steps=row.steps,
            visitor_count=row.session_count,
            percentage=round(row.session_count / total_sessions * 100, 2)
            if total_sessions
            else 0.0,
        )
        for row in path_rows
    ]

    response = NavigationOverviewResponse(
        top_paths=top_paths,
        average_pages_per_session=round(avg_pages, 2),
        exit_rates=[
            ExitRateByPage(path=r.path, exits=r.exits, exit_rate_pct=r.exit_rate_pct)
            for r in exit_rate_rows
        ],
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.LONG)
    logger.info("Navigation overview computed and cached")
    return response