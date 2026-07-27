"""
Filters route -- returns filter options for populating dashboard UI
controls (dropdowns, date pickers, multi-selects).

Requires a valid bearer token, same as every other dashboard route.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.filters import FilterOptionsResponse
from app.services.filters_service import get_filter_options

router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("", response_model=FilterOptionsResponse)
async def get_filter_options_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> FilterOptionsResponse:
    return await get_filter_options()