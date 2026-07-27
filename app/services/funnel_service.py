"""
Funnel intelligence business logic.

Computes conversion rates from raw repository counts and caches
each of the four sections independently in Redis -- they're
different queries with different costs, so caching them separately
(rather than one combined blob) lets each section's cache expire
and refresh on its own schedule.
"""

import logging

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.funnel_repository import (
    get_cohort_comparison,
    get_content_influence,
    get_dropoff_timing,
    get_source_attribution,
)
from app.schemas.funnel import (
    CohortComparisonResponse,
    CohortStats,
    ContentInfluence,
    ContentInfluenceResponse,
    DropoffTimingBucket,
    DropoffTimingResponse,
    SourceAttribution,
    SourceAttributionResponse,
)

logger = logging.getLogger(__name__)


def _conversion_rate(converters: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(converters / total * 100, 2)


async def _get_cached(key: str) -> str | None:
    redis = await get_redis()
    return await redis.get(key)


async def _set_cached(key: str, value: str, ttl_seconds: int) -> None:
    redis = await get_redis()
    await redis.set(key, value, ex=ttl_seconds)


async def get_source_attribution_summary() -> SourceAttributionResponse:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "funnel", "source_attribution")
    cached = await _get_cached(cache_key)
    if cached is not None:
        return SourceAttributionResponse.model_validate_json(cached)

    rows = await get_source_attribution()
    response = SourceAttributionResponse(
        sources=[
            SourceAttribution(
                source=row.source,
                total_users=row.total_users,
                converters=row.converters,
                conversion_rate_pct=_conversion_rate(row.converters, row.total_users),
            )
            for row in rows
        ]
    )
    await _set_cached(cache_key, response.model_dump_json(), CacheTTL.MEDIUM)
    return response


async def get_content_influence_summary() -> ContentInfluenceResponse:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "funnel", "content_influence")
    cached = await _get_cached(cache_key)
    if cached is not None:
        return ContentInfluenceResponse.model_validate_json(cached)

    rows = await get_content_influence()
    response = ContentInfluenceResponse(
        pages=[
            ContentInfluence(
                page_path=row.page_path,
                total_visitors=row.total_visitors,
                converters=row.converters,
                conversion_rate_pct=_conversion_rate(row.converters, row.total_visitors),
            )
            for row in rows
        ]
    )
    await _set_cached(cache_key, response.model_dump_json(), CacheTTL.MEDIUM)
    return response


async def get_cohort_comparison_summary() -> CohortComparisonResponse:
    # Longer TTL -- behavioral cohort averages shift slowly.
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "funnel", "cohort_comparison")
    cached = await _get_cached(cache_key)
    if cached is not None:
        return CohortComparisonResponse.model_validate_json(cached)

    rows = await get_cohort_comparison()
    response = CohortComparisonResponse(
        cohorts=[
            CohortStats(
                cohort=row.cohort,
                avg_events=row.avg_events,
                avg_pages_visited=row.avg_pages_visited,
            )
            for row in rows
        ]
    )
    await _set_cached(cache_key, response.model_dump_json(), CacheTTL.LONG)
    return response


async def get_dropoff_timing_summary() -> DropoffTimingResponse:
    # Shorter TTL -- this is closer to "live" operational data used
    # to time same-day re-engagement campaigns.
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "funnel", "dropoff_timing")
    cached = await _get_cached(cache_key)
    if cached is not None:
        return DropoffTimingResponse.model_validate_json(cached)

    rows = await get_dropoff_timing()
    response = DropoffTimingResponse(
        buckets=[
            DropoffTimingBucket(
                hour_of_day=row.hour_of_day,
                users_dropping_off=row.users_dropping_off,
                dropoff_events=row.dropoff_events,
            )
            for row in rows
        ]
    )
    await _set_cached(cache_key, response.model_dump_json(), CacheTTL.SHORT)
    return response