"""
Traffic & Overview business logic.

First real (non-mock) Phase 12 service. Orchestrates the five
traffic_repository queries concurrently and caches the combined
result as one JSON blob, since a dashboard load always needs all
five pieces together -- caching them separately would let them
drift out of sync with each other under load.
"""

import asyncio
import logging

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.traffic_repository import (
    get_device_breakdown,
    get_platform_breakdown,
    get_top_pages,
    get_total_page_views,
    get_unique_visitors,
)
from app.schemas.traffic import (
    DeviceBreakdown,
    PlatformBreakdown,
    TopPage,
    TrafficOverviewResponse,
)

logger = logging.getLogger(__name__)

_TOP_PAGES_LIMIT = 10


async def get_traffic_overview() -> TrafficOverviewResponse:
    """Returns the Traffic & Overview summary, served from cache when available."""
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "traffic", "overview")
    redis = await get_redis()

    cached = await redis.get(cache_key)
    if cached is not None:
        logger.info("Traffic overview served from cache")
        return TrafficOverviewResponse.model_validate_json(cached)

    total_views, unique_visitors, top_pages_rows, device_row, platform_rows = (
        await asyncio.gather(
            get_total_page_views(),
            get_unique_visitors(),
            get_top_pages(_TOP_PAGES_LIMIT),
            get_device_breakdown(),
            get_platform_breakdown(),
        )
    )

    response = TrafficOverviewResponse(
        total_page_views=total_views,
        unique_visitors=unique_visitors,
        top_pages=[
            TopPage(path=r.path, title=r.title, views=r.views) for r in top_pages_rows
        ],
        device_breakdown=DeviceBreakdown(
            mobile=device_row.mobile,
            desktop=device_row.desktop,
            unknown=device_row.unknown,
        ),
        platform_breakdown=[
            PlatformBreakdown(platform=r.platform, views=r.views) for r in platform_rows
        ],
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.MEDIUM)
    logger.info("Traffic overview computed and cached")
    return response