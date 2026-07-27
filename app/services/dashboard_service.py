"""
Dashboard business logic: KPI summary and conversion funnel.

Both endpoints are cached in Redis, since they're aggregate queries
over potentially large tables that dashboards refresh frequently but
whose underlying data doesn't change second-to-second.
"""

import json
import logging

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.dashboard_repository import get_funnel_steps, get_kpis
from app.schemas.dashboard import FunnelResponse, FunnelStep, KpiSummary

logger = logging.getLogger(__name__)


async def _get_cached(key: str) -> str | None:
    redis = await get_redis()
    return await redis.get(key)


async def _set_cached(key: str, value: str, ttl_seconds: int) -> None:
    redis = await get_redis()
    await redis.set(key, value, ex=ttl_seconds)


async def get_kpi_summary() -> KpiSummary:
    """Returns the dashboard KPI row, served from cache when available."""
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "dashboard", "kpis")

    cached = await _get_cached(cache_key)
    if cached is not None:
        logger.info("KPI summary served from cache")
        return KpiSummary.model_validate_json(cached)

    row = await get_kpis()
    summary = KpiSummary(
        total_users=row.total_users,
        total_orders=row.total_orders,
        total_revenue=row.total_revenue,
        avg_order_value=row.avg_order_value,
        total_signups=row.total_signups,
        total_form_submissions=row.total_form_submissions,
    )

    await _set_cached(cache_key, summary.model_dump_json(), CacheTTL.MEDIUM)
    logger.info("KPI summary computed and cached")
    return summary


async def get_funnel() -> FunnelResponse:
    """
    Returns the conversion funnel with dropoff/conversion percentages
    computed relative to the previous step and the top-of-funnel step.
    """
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "dashboard", "funnel")

    cached = await _get_cached(cache_key)
    if cached is not None:
        logger.info("Funnel served from cache")
        return FunnelResponse.model_validate_json(cached)

    rows = await get_funnel_steps()

    if not rows:
        response = FunnelResponse(steps=[])
        await _set_cached(cache_key, response.model_dump_json(), CacheTTL.MEDIUM)
        return response

    top_users = rows[0].users
    steps: list[FunnelStep] = []
    previous_users = None

    for row in rows:
        if previous_users is None or previous_users == 0:
            dropoff_pct = 0.0
        else:
            # Clamp at 0 -- if a later step has MORE users than the
            # previous one (messy real-world tracking gaps, as seen
            # in the mock data), that's a data quality signal, not
            # a negative dropoff.
            dropoff_pct = max(0.0, round((previous_users - row.users) / previous_users * 100, 2))

        conversion_from_top = (
            round(row.users / top_users * 100, 2) if top_users > 0 else 0.0
        )

        steps.append(
            FunnelStep(
                event_name=row.event_name,
                users=row.users,
                dropoff_pct=dropoff_pct,
                conversion_from_top=conversion_from_top,
            )
        )
        previous_users = row.users

    response = FunnelResponse(steps=steps)
    await _set_cached(cache_key, response.model_dump_json(), CacheTTL.MEDIUM)
    logger.info("Funnel computed and cached")
    return response