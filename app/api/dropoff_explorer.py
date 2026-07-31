"""
Drop-off Explorer routes -- exportable list of specific visitors who
dropped off between two real funnel stages, for follow-up.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.dropoff_explorer import DropoffSummary, DropoffVisitor
from app.services.dropoff_explorer_service import (
    InvalidFunnelStepError,
    get_dropoff_summary,
    get_dropoff_visitors_page,
)

router = APIRouter(prefix="/dropoff-explorer", tags=["dropoff-explorer"])


@router.get("/summary", response_model=DropoffSummary)
async def get_dropoff_summary_route(
    from_step: str = Query(..., max_length=50),
    to_step: str = Query(..., max_length=50),
    start_date: date | None = Query(default=None, description="Inclusive start of date range"),
    end_date: date | None = Query(default=None, description="Inclusive end of date range"),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> DropoffSummary:
    try:
        return await get_dropoff_summary(from_step, to_step, start_date, end_date)
    except InvalidFunnelStepError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "code": "INVALID_FUNNEL_STEP"},
        )


@router.get("/visitors", response_model=PaginatedResponse[DropoffVisitor])
async def get_dropoff_visitors_route(
    from_step: str = Query(..., max_length=50),
    to_step: str = Query(..., max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    start_date: date | None = Query(default=None, description="Inclusive start of date range"),
    end_date: date | None = Query(default=None, description="Inclusive end of date range"),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[DropoffVisitor]:
    try:
        return await get_dropoff_visitors_page(
            from_step, to_step, page=page, page_size=page_size,
            start_date=start_date, end_date=end_date,
        )
    except InvalidFunnelStepError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "code": "INVALID_FUNNEL_STEP"},
        )