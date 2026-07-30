"""
Traffic & Overview business logic.

First real (non-mock) Phase 12 service. Orchestrates the five
traffic_repository queries concurrently and caches the combined
result as one JSON blob, since a dashboard load always needs all
five pieces together -- caching them separately would let them
drift out of sync with each other under load.

Now accepts an optional date range -- each distinct range gets its
own cache entry, since "all time" and "last 7 days" are genuinely
different answers, not variations of the same one.
"""

import asyncio
import logging
from datetime import date

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


def _date_cache_segment(start_date: date | None, end_date: date | None) -> str:
    """Turns an optional date range into a stable Redis key segment."""
    start_str = start_date.isoformat() if start_date else "all"
    end_str = end_date.isoformat() if end_date else "all"
    return f"{start_str}_{end_str}"


async def get_traffic_overview(
    start_date: date | None = None, end_date: date | None = None
) -> TrafficOverviewResponse:
    """Returns the Traffic & Overview summary, served from cache when available."""
    cache_key = build_redis_key(
        RedisKeyPrefix.CACHE, "traffic", "overview", _date_cache_segment(start_date, end_date)
    )
    redis = await get_redis()

    cached = await redis.get(cache_key)
    if cached is not None:
        logger.info("Traffic overview served from cache")
        return TrafficOverviewResponse.model_validate_json(cached)

    total_views, unique_visitors, top_pages_rows, device_row, platform_rows = (
        await asyncio.gather(
            get_total_page_views(start_date, end_date),
            get_unique_visitors(start_date, end_date),
            get_top_pages(_TOP_PAGES_LIMIT, start_date, end_date),
            get_device_breakdown(start_date, end_date),
            get_platform_breakdown(start_date, end_date),
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