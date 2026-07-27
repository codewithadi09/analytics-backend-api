"""
Filters business logic.

Combines static constants (funnel steps, event names) with
repository data (traffic sources, date range) into one response
the frontend fetches once to populate every dashboard's filter UI.
Long cache TTL since these options change infrequently.
"""

import logging

from app.core.constants import CacheTTL, EventName, FUNNEL_STEPS, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.filters_repository import get_date_range, get_traffic_sources
from app.schemas.filters import DateRange, FilterOptionsResponse

logger = logging.getLogger(__name__)


async def get_filter_options() -> FilterOptionsResponse:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "filters", "options")

    redis = await get_redis()
    cached = await redis.get(cache_key)
    if cached is not None:
        return FilterOptionsResponse.model_validate_json(cached)

    sources = await get_traffic_sources()
    date_range_row = await get_date_range()

    response = FilterOptionsResponse(
        funnel_steps=FUNNEL_STEPS,
        event_names=[e.value for e in EventName],
        traffic_sources=sources,
        date_range=DateRange(
            earliest_event=date_range_row.earliest_event,
            latest_event=date_range_row.latest_event,
        ),
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.LONG)
    return response