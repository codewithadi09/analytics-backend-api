"""
Users routes -- dropoff explorer and recent orders.

All routes require a valid bearer token.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import require_rate_limit
from app.core.constants import FUNNEL_STEPS
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.users import DropoffSummary, DropoffUser, RecentOrder
from app.services.users_service import (
    get_dropoff_summary,
    get_dropoff_users_page,
    get_recent_orders_page,
)

router = APIRouter(prefix="/users", tags=["users"])


def _validate_funnel_steps(from_step: str, to_step: str) -> None:
    if from_step not in FUNNEL_STEPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": f"Invalid from_step: {from_step}", "code": "INVALID_FUNNEL_STEP"},
        )
    if to_step not in FUNNEL_STEPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": f"Invalid to_step: {to_step}", "code": "INVALID_FUNNEL_STEP"},
        )
    if from_step == to_step:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "from_step and to_step must differ", "code": "INVALID_FUNNEL_STEP"},
        )


@router.get("/dropoff/summary", response_model=DropoffSummary)
async def get_dropoff_summary_route(
    from_step: str = Query(...),
    to_step: str = Query(...),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> DropoffSummary:
    _validate_funnel_steps(from_step, to_step)
    return await get_dropoff_summary(from_step, to_step)


@router.get("/dropoff", response_model=PaginatedResponse[DropoffUser])
async def get_dropoff_users_route(
    from_step: str = Query(...),
    to_step: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[DropoffUser]:
    _validate_funnel_steps(from_step, to_step)
    return await get_dropoff_users_page(from_step, to_step, page=page, page_size=page_size)


@router.get("/orders/recent", response_model=PaginatedResponse[RecentOrder])
async def get_recent_orders_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[RecentOrder]:
    return await get_recent_orders_page(page=page, page_size=page_size)