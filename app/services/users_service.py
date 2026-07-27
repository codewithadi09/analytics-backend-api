"""
Users business logic: dropoff explorer and recent orders.

Both are paginated PII-bearing lists, following the same pattern
as retention_service.py. Not cached in Redis -- dropoff results
are parameterized by from_step/to_step (would need a cache key per
combination, low value for a dashboard explorer tool), and recent
orders should reflect near-real-time state rather than a stale
cached snapshot.
"""

import logging

from app.repositories.users_repository import (
    get_dropoff_users as repo_get_dropoff_users,
    get_recent_orders as repo_get_recent_orders,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.users import DropoffSummary, DropoffUser, RecentOrder

logger = logging.getLogger(__name__)


def _paginate(items: list, page: int, page_size: int) -> tuple[list, PaginationMeta]:
    total_items = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    meta = PaginationMeta.build(page=page, page_size=page_size, total_items=total_items)
    return page_items, meta


async def get_dropoff_summary(from_step: str, to_step: str) -> DropoffSummary:
    """Summary counts for the dropoff explorer's metric cards."""
    rows = await repo_get_dropoff_users(from_step, to_step)
    identified_count = sum(1 for r in rows if r.email)
    anonymous_count = len(rows) - identified_count

    return DropoffSummary(
        from_step=from_step,
        to_step=to_step,
        total_dropoff=len(rows),
        identified_count=identified_count,
        anonymous_count=anonymous_count,
    )


async def get_dropoff_users_page(
    from_step: str, to_step: str, page: int, page_size: int
) -> PaginatedResponse[DropoffUser]:
    rows = await repo_get_dropoff_users(from_step, to_step)
    page_rows, meta = _paginate(rows, page, page_size)

    items = [
        DropoffUser(
            user_id=r.user_id,
            email=r.email,
            user_name=r.user_name,
            last_seen=r.last_seen,
        )
        for r in page_rows
    ]
    return PaginatedResponse[DropoffUser](items=items, meta=meta)


async def get_recent_orders_page(page: int, page_size: int) -> PaginatedResponse[RecentOrder]:
    rows = await repo_get_recent_orders()
    page_rows, meta = _paginate(rows, page, page_size)

    items = [
        RecentOrder(
            order_id=r.order_id,
            email=r.email,
            user_name=r.user_name,
            order_total=r.order_total,
            order_date=r.order_date,
            status=r.status,
        )
        for r in page_rows
    ]
    return PaginatedResponse[RecentOrder](items=items, meta=meta)