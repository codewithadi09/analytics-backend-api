"""
Interactions / Click Analytics routes -- unified leaderboard and
drill-down events across all 16 real click-interaction tables.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.interactions import InteractionEvent, InteractionLeaderboardResponse
from app.services.interactions_service import (
    InvalidInteractionTypeError,
    get_interaction_events_page,
    get_interaction_leaderboard,
)

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("/leaderboard", response_model=InteractionLeaderboardResponse)
async def get_interaction_leaderboard_route(
    start_date: date | None = Query(default=None, description="Inclusive start of date range"),
    end_date: date | None = Query(default=None, description="Inclusive end of date range"),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> InteractionLeaderboardResponse:
    return await get_interaction_leaderboard(start_date, end_date)


@router.get("/events", response_model=PaginatedResponse[InteractionEvent])
async def get_interaction_events_route(
    interaction_type: str | None = Query(default=None, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    start_date: date | None = Query(default=None, description="Inclusive start of date range"),
    end_date: date | None = Query(default=None, description="Inclusive end of date range"),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> PaginatedResponse[InteractionEvent]:
    try:
        return await get_interaction_events_page(
            interaction_type=interaction_type,
            page=page,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date,
        )
    except InvalidInteractionTypeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Invalid interaction_type: {interaction_type}",
                "code": "INVALID_INTERACTION_TYPE",
            },
        )