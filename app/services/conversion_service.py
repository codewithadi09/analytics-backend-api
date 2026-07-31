"""
Conversion Funnel (real) business logic.

Computes dropoff/conversion percentages from raw repository counts,
same shape as the old mock dashboard_service.py's get_funnel(). Same
clamping convention carried forward: if a later step has MORE users
than the step before it, dropoff_pct is clamped at 0 rather than
shown as negative.

This clamp is expected to matter MORE here than it did on the old
mock data -- confirmed in testing that form_field_complete can
exceed form_start, almost certainly because a visitor's form_start
event wasn't captured due to a client-side tracking gap (the same
category of gap flagged in the handoff doc's Known Limitations
section), not because completion genuinely precedes starting.
"""

import logging
from datetime import date

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.conversion_repository import get_funnel_step_counts
from app.schemas.conversion import ConversionFunnelResponse, ConversionFunnelStep

logger = logging.getLogger(__name__)


def _date_cache_segment(start_date: date | None, end_date: date | None) -> str:
    start_str = start_date.isoformat() if start_date else "all"
    end_str = end_date.isoformat() if end_date else "all"
    return f"{start_str}_{end_str}"


async def get_conversion_funnel(
    start_date: date | None = None, end_date: date | None = None
) -> ConversionFunnelResponse:
    cache_key = build_redis_key(
        RedisKeyPrefix.CACHE, "conversion", "funnel", _date_cache_segment(start_date, end_date)
    )
    redis = await get_redis()

    cached = await redis.get(cache_key)
    if cached is not None:
        logger.info("Conversion funnel served from cache")
        return ConversionFunnelResponse.model_validate_json(cached)

    rows = await get_funnel_step_counts(start_date, end_date)

    if not rows:
        response = ConversionFunnelResponse(steps=[])
        await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.MEDIUM)
        return response

    top_users = rows[0].users
    steps: list[ConversionFunnelStep] = []
    previous_users = None

    for row in rows:
        if previous_users is None or previous_users == 0:
            dropoff_pct = 0.0
        else:
            dropoff_pct = max(0.0, round((previous_users - row.users) / previous_users * 100, 2))

        conversion_from_top = (
            round(row.users / top_users * 100, 2) if top_users > 0 else 0.0
        )

        steps.append(
            ConversionFunnelStep(
                step_name=row.step_name,
                users=row.users,
                dropoff_pct=dropoff_pct,
                conversion_from_top=conversion_from_top,
            )
        )
        previous_users = row.users

    response = ConversionFunnelResponse(steps=steps)
    await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.MEDIUM)
    logger.info("Conversion funnel computed and cached")
    return response