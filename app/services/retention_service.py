"""
Retention business logic.

Churned users and revenue-per-user are paginated (both are PII-
bearing lists that could grow large); re-engagement and retention
curve are small aggregates cached and returned in full.
"""

import logging

from app.core.constants import CacheTTL, RedisKeyPrefix, build_redis_key
from app.core.redis_client import get_redis
from app.repositories.retention_repository import (
    get_churned_users as repo_get_churned_users,
    get_reengaged_users as repo_get_reengaged_users,
    get_retention_curve as repo_get_retention_curve,
    get_revenue_per_user as repo_get_revenue_per_user,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.retention import (
    ChurnedUser,
    ReengagedUser,
    ReengagedUsersResponse,
    RetentionCurvePoint,
    RetentionCurveResponse,
    UserRevenue,
)

logger = logging.getLogger(__name__)


async def _get_cached(key: str) -> str | None:
    redis = await get_redis()
    return await redis.get(key)


async def _set_cached(key: str, value: str, ttl_seconds: int) -> None:
    redis = await get_redis()
    await redis.set(key, value, ex=ttl_seconds)


def _paginate(items: list, page: int, page_size: int) -> tuple[list, PaginationMeta]:
    total_items = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    meta = PaginationMeta.build(page=page, page_size=page_size, total_items=total_items)
    return page_items, meta


async def get_churned_users_page(page: int, page_size: int) -> PaginatedResponse[ChurnedUser]:
    # Cache the full underlying list (cheap, bounded in this mock;
    # in Phase 12 this stays a single query, with pagination applied
    # in-memory here rather than re-querying Postgres per page --
    # fine at moderate scale, revisit with DB-side LIMIT/OFFSET if
    # the churned-user table ever grows very large).
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "retention", "churned_users")
    cached = await _get_cached(cache_key)

    if cached is not None:
        import json
        rows = json.loads(cached)
    else:
        raw_rows = await repo_get_churned_users()
        rows = [
            {
                "email": r.email,
                "user_name": r.user_name,
                "last_seen": r.last_seen,
                "total_orders": r.total_orders,
                "lifetime_revenue": r.lifetime_revenue,
                "inactive_for": r.inactive_for,
            }
            for r in raw_rows
        ]
        import json
        await _set_cached(cache_key, json.dumps(rows), CacheTTL.MEDIUM)

    page_rows, meta = _paginate(rows, page, page_size)
    items = [ChurnedUser(**row) for row in page_rows]
    return PaginatedResponse[ChurnedUser](items=items, meta=meta)


async def get_reengaged_users_summary() -> ReengagedUsersResponse:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "retention", "reengaged_users")
    cached = await _get_cached(cache_key)
    if cached is not None:
        return ReengagedUsersResponse.model_validate_json(cached)

    rows = await repo_get_reengaged_users()
    users = [
        ReengagedUser(
            email=r.email,
            user_name=r.user_name,
            went_dark_at=r.went_dark_at,
            came_back_at=r.came_back_at,
            gap_hours=r.gap_hours,
        )
        for r in rows
    ]
    avg_gap = round(sum(r.gap_hours for r in rows) / len(rows), 2) if rows else 0.0

    response = ReengagedUsersResponse(users=users, avg_gap_hours=avg_gap)
    await _set_cached(cache_key, response.model_dump_json(), CacheTTL.MEDIUM)
    return response


async def get_revenue_per_user_page(page: int, page_size: int) -> PaginatedResponse[UserRevenue]:
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "retention", "revenue_per_user")
    cached = await _get_cached(cache_key)

    if cached is not None:
        import json
        rows = json.loads(cached)
    else:
        raw_rows = await repo_get_revenue_per_user()
        rows = [
            {
                "email": r.email,
                "user_name": r.user_name,
                "total_orders": r.total_orders,
                "lifetime_revenue": r.lifetime_revenue,
                "avg_order_value": r.avg_order_value,
                "first_order": r.first_order,
                "last_order": r.last_order,
            }
            for r in raw_rows
        ]
        import json
        await _set_cached(cache_key, json.dumps(rows), CacheTTL.MEDIUM)

    page_rows, meta = _paginate(rows, page, page_size)
    items = [UserRevenue(**row) for row in page_rows]
    return PaginatedResponse[UserRevenue](items=items, meta=meta)


async def get_retention_curve_summary() -> RetentionCurveResponse:
    # Longer TTL -- retention curves shift slowly day to day.
    cache_key = build_redis_key(RedisKeyPrefix.CACHE, "retention", "curve")
    cached = await _get_cached(cache_key)
    if cached is not None:
        return RetentionCurveResponse.model_validate_json(cached)

    rows = await repo_get_retention_curve()
    response = RetentionCurveResponse(
        points=[
            RetentionCurvePoint(
                days_since_first_visit=r.days_since_first_visit,
                retention_pct=r.retention_pct,
                retained_users=r.retained_users,
            )
            for r in rows
        ]
    )
    await _set_cached(cache_key, response.model_dump_json(), CacheTTL.LONG)
    return response