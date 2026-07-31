"""
User Journey (cross-session) routes.

/visitors (a literal path) is registered BEFORE /{anonymous_id} (a
parameterized path) deliberately -- FastAPI matches routes in
registration order, so reversing this would make "/journey/visitors"
get swallowed as if "visitors" were someone's anonymous_id. This is
the exact route-ordering bug class flagged in this project's own
handoff notes from Phase 8/9.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.journey import UserJourneyResponse, VisitorSummary
from app.services.journey_service import (
    UserNotFoundError,
    get_user_journey,
    get_visitors_page,
)

router = APIRouter(prefix="/journey", tags=["journey"])


@router.get("/visitors", response_model=PaginatedResponse[VisitorSummary])
async def get_visitors_route(
    search: str | None = Query(default=None, max_length=254),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[VisitorSummary]:
    return await get_visitors_page(search=search, page=page, page_size=page_size)


@router.get("/{anonymous_id}", response_model=UserJourneyResponse)
async def get_user_journey_route(
    anonymous_id: str = Path(..., min_length=3, max_length=254),
    sort_order: Literal["asc", "desc"] = Query(
        default="asc",
        description="asc = oldest first (default), desc = newest first",
    ),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> UserJourneyResponse:
    try:
        return await get_user_journey(anonymous_id, sort_order)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No journey found for this visitor", "code": "USER_NOT_FOUND"},
        )