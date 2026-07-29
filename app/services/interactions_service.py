"""
Interactions / Click Analytics business logic.

Leaderboard (aggregate across all 16 tables) is cached -- every
dashboard load requests it identically. The paginated events list is
NOT cached, same reasoning as the old users_service.py dropoff
explorer: parameterized by type+page, low cache hit-rate value, and
should reflect near-real-time data for drill-down use.
"""

import logging

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.interactions_repository import (
    VALID_INTERACTION_TYPES,
    get_interaction_counts,
    get_interactions_page as repo_get_interactions_page,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.interactions import (
    InteractionEvent,
    InteractionLeaderboardResponse,
    InteractionTypeCount,
)

logger = logging.getLogger(__name__)


class InvalidInteractionTypeError(Exception):
    """Raised when interaction_type isn't one of the 16 known click tables."""


async def get_interaction_leaderboard() -> InteractionLeaderboardResponse:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "interactions", "leaderboard")
    redis = await get_redis()

    cached = await redis.get(cache_key)
    if cached is not None:
        logger.info("Interaction leaderboard served from cache")
        return InteractionLeaderboardResponse.model_validate_json(cached)

    rows = await get_interaction_counts()
    by_type = [
        InteractionTypeCount(interaction_type=r.interaction_type, count=r.count)
        for r in rows
    ]
    response = InteractionLeaderboardResponse(
        total_interactions=sum(r.count for r in rows),
        by_type=by_type,
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CacheTTL.MEDIUM)
    logger.info("Interaction leaderboard computed and cached")
    return response


async def get_interaction_events_page(
    interaction_type: str | None, page: int, page_size: int
) -> PaginatedResponse[InteractionEvent]:
    """
    Not cached -- see module docstring. Raises InvalidInteractionTypeError
    if interaction_type is provided but isn't one of the 16 known tables.
    """
    if interaction_type is not None and interaction_type not in VALID_INTERACTION_TYPES:
        raise InvalidInteractionTypeError(
            f"Unknown interaction_type: {interaction_type}"
        )

    offset = (page - 1) * page_size
    rows = await repo_get_interactions_page(
        interaction_type=interaction_type, limit=page_size, offset=offset
    )

    items = [
        InteractionEvent(
            interaction_type=r.interaction_type,
            label=r.label,
            page_path=r.page_path,
            timestamp=r.timestamp,
        )
        for r in rows
    ]

    # Note: total_items here is a page-fetch-based estimate, not a true
    # COUNT(*) -- computing an exact total across a 16-table UNION ALL
    # (or a single filtered table) on every page request is unnecessary
    # cost for a drill-down list. meta.total_pages/total_items won't be
    # exact when a type filter is applied; fine for this use case, but
    # worth knowing if the frontend ever relies on those numbers being precise.
    meta = PaginationMeta.build(page=page, page_size=page_size, total_items=len(items) + offset)
    return PaginatedResponse[InteractionEvent](items=items, meta=meta)