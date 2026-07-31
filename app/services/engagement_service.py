"""
Services & Content Engagement business logic.

Combines three independent queries (page engagement, milestone
breakdown, content engagement) concurrently and caches the result as
one blob, same reasoning as Domain 1: a dashboard load always needs
all three pieces together. Cached per date range, same pattern as
every other filtered domain.
"""

import asyncio
import logging
from datetime import date

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.engagement_repository import (
    get_content_engagement,
    get_milestone_breakdown,
    get_page_engagement,
)
from app.schemas.engagement import (
    ContentEngagementItem,
    EngagementMilestoneBucket,
    PageEngagement,
    ServicesContentEngagementResponse,
)

logger = logging.getLogger(__name__)


def _date_cache_segment(start_date: date | None, end_date: date | None) -> str:
    start_str = start_date.isoformat() if start_date else "all"
    end_str = end_date.isoformat() if end_date else "all"
    return f"{start_str}_{end_str}"


async def get_engagement_overview(
    start_date: date | None = None, end_date: date | None = None
) -> ServicesContentEngagementResponse:
    cache_key = build_redis_key(
        RedisKeyPrefix.CACHE, "engagement", "overview", _date_cache_segment(start_date, end_date)
    )
    redis = await get_redis()

    cached = await redis.get(cache_key)
    if cached is not None:
        logger.info("Engagement overview served from cache")
        return ServicesContentEngagementResponse.model_validate_json(cached)

    page_rows, milestone_rows, content_rows = await asyncio.gather(
        get_page_engagement(start_date, end_date),
        get_milestone_breakdown(start_date, end_date),
        get_content_engagement(start_date, end_date),
    )

    response = ServicesContentEngagementResponse(
        page_engagement=[
            PageEngagement(
                path=r.path,
                views=r.views,
                avg_scroll_depth_pct=r.avg_scroll_depth_pct,
                median_scroll_depth_pct=r.median_scroll_depth_pct,
                engaged_visit_count=r.engaged_visit_count,
            )
            for r in page_rows
        ],
        milestone_breakdown=[
            EngagementMilestoneBucket(
                milestone_seconds=r.milestone_seconds, visit_count=r.visit_count
            )
            for r in milestone_rows
        ],
        content_engagement=[
            ContentEngagementItem(
                content_type=r.content_type, label=r.label, url=r.url, clicks=r.clicks
            )
            for r in content_rows
        ],
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.MEDIUM)
    logger.info("Engagement overview computed and cached")
    return response