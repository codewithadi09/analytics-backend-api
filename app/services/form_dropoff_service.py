"""
Form Field Drop-off business logic.

dropoff_pct clamped at 0 (same convention as Domain 6's conversion
funnel) in case a data gap ever makes complete_count exceed
focus_count for a field. most_common_dropoff_field is chosen by raw
dropoff COUNT, not percentage -- a low-traffic field can have a high
percentage without being where most real people actually get stuck.
"""

import logging

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.form_dropoff_repository import get_field_dropoff_stats
from app.schemas.form_dropoff import FieldDropoff, FormFieldDropoffResponse

logger = logging.getLogger(__name__)


async def get_form_dropoff_overview() -> FormFieldDropoffResponse:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "form_dropoff", "overview")
    redis = await get_redis()

    cached = await redis.get(cache_key)
    if cached is not None:
        logger.info("Form dropoff overview served from cache")
        return FormFieldDropoffResponse.model_validate_json(cached)

    rows = await get_field_dropoff_stats()

    fields: list[FieldDropoff] = []
    most_common_field: str | None = None
    highest_raw_dropoff = -1

    for row in rows:
        raw_dropoff = max(0, row.focus_count - row.complete_count)
        dropoff_pct = (
            round(raw_dropoff / row.focus_count * 100, 2) if row.focus_count > 0 else 0.0
        )

        fields.append(
            FieldDropoff(
                field_name=row.field_name,
                focus_count=row.focus_count,
                complete_count=row.complete_count,
                error_count=row.error_count,
                dropoff_pct=dropoff_pct,
                avg_time_seconds=row.avg_time_seconds,
            )
        )

        if raw_dropoff > highest_raw_dropoff:
            highest_raw_dropoff = raw_dropoff
            most_common_field = row.field_name

    # Only report a "most common dropoff field" if at least one visitor
    # actually dropped off somewhere -- otherwise every field is at 0
    # raw dropoff and naming one as "most common" would be misleading.
    if highest_raw_dropoff <= 0:
        most_common_field = None

    response = FormFieldDropoffResponse(
        fields=fields, most_common_dropoff_field=most_common_field
    )
    await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.MEDIUM)
    logger.info("Form dropoff overview computed and cached")
    return response