"""
Traffic & Overview routes -- first real (non-mock) Phase 12 domain.

Single endpoint answering "what does our traffic look like": total
views, unique visitors, top pages, device/platform breakdown. All
sourced from the real pages table, cached via traffic_service.

start_date/end_date are optional -- omitting both returns all-time
data, matching the original behavior before date filtering existed.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.traffic import TrafficOverviewResponse
from app.services.traffic_service import get_traffic_overview

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/overview", response_model=TrafficOverviewResponse)
async def get_traffic_overview_route(
    start_date: date | None = Query(default=None, description="Inclusive start of date range"),
    end_date: date | None = Query(default=None, description="Inclusive end of date range"),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> TrafficOverviewResponse:
    return await get_traffic_overview(start_date, end_date)