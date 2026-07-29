"""
Drop-off Explorer routes -- exportable list of specific visitors who
dropped off between two real funnel stages, for follow-up.
"""

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
    current_user: CurrentUser = Depends(require_rate_limit),
) -> DropoffSummary:
    try:
        return await get_dropoff_summary(from_step, to_step)
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
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[DropoffVisitor]:
    try:
        return await get_dropoff_visitors_page(from_step, to_step, page=page, page_size=page_size)
    except InvalidFunnelStepError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "code": "INVALID_FUNNEL_STEP"},
        )