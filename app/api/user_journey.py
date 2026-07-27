"""
User journey routes -- identified users list, dataset counts, and
a single user's full event timeline.

All routes require a valid bearer token.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.user_journey import IdentifiedUser, UserCounts, UserJourneyResponse
from app.services.user_journey_service import (
    UserNotFoundError,
    get_dataset_counts,
    get_identified_users,
    get_journey,
)

router = APIRouter(prefix="/users", tags=["user-journey"])


@router.get("", response_model=list[IdentifiedUser])
async def list_identified_users_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> list[IdentifiedUser]:
    return await get_identified_users()


@router.get("/counts", response_model=UserCounts)
async def get_user_counts_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> UserCounts:
    return await get_dataset_counts()


@router.get("/{user_id}/journey", response_model=UserJourneyResponse)
async def get_user_journey_route(
    user_id: str,
    current_user: CurrentUser = Depends(require_rate_limit),
) -> UserJourneyResponse:
    try:
        return await get_journey(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No journey found for this user", "code": "USER_NOT_FOUND"},
        )