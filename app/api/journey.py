"""
User Journey (cross-session) routes -- a single visitor's full
chronological timeline across pages, all 16 click tables, and the
form funnel, looked up by anonymous_id.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.journey import UserJourneyResponse
from app.services.journey_service import UserNotFoundError, get_user_journey

router = APIRouter(prefix="/journey", tags=["journey"])


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