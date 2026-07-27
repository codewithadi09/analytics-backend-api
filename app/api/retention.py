"""
Retention routes -- churned users, re-engagement, revenue per user,
and the retention curve.

All routes require a valid bearer token. Churned users and revenue
per user are paginated via ?page= and ?page_size= query params.
"""

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.retention import (
    ChurnedUser,
    ReengagedUsersResponse,
    RetentionCurveResponse,
    UserRevenue,
)
from app.services.retention_service import (
    get_churned_users_page,
    get_reengaged_users_summary,
    get_retention_curve_summary,
    get_revenue_per_user_page,
)

router = APIRouter(prefix="/retention", tags=["retention"])


@router.get("/churned", response_model=PaginatedResponse[ChurnedUser])
async def get_churned_users_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[ChurnedUser]:
    return await get_churned_users_page(page=page, page_size=page_size)


@router.get("/reengaged", response_model=ReengagedUsersResponse)
async def get_reengaged_users_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> ReengagedUsersResponse:
    return await get_reengaged_users_summary()


@router.get("/revenue-per-user", response_model=PaginatedResponse[UserRevenue])
async def get_revenue_per_user_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[UserRevenue]:
    return await get_revenue_per_user_page(page=page, page_size=page_size)


@router.get("/curve", response_model=RetentionCurveResponse)
async def get_retention_curve_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> RetentionCurveResponse:
    return await get_retention_curve_summary()