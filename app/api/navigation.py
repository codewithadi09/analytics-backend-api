"""
Navigation Path Analysis routes -- common multi-step routes visitors
take through the site, average pages per session, and per-page exit
rates. All from the real pages table, reconstructed via session
(anonymous_id + context_session_id) sequencing.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.navigation import NavigationOverviewResponse
from app.services.navigation_service import get_navigation_overview

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.get("/overview", response_model=NavigationOverviewResponse)
async def get_navigation_overview_route(
    start_date: date | None = Query(default=None, description="Inclusive start of date range"),
    end_date: date | None = Query(default=None, description="Inclusive end of date range"),
    current_user: CurrentUser = Depends(require_rate_limit),
) -> NavigationOverviewResponse:
    return await get_navigation_overview(start_date, end_date)