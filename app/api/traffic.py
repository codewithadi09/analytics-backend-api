"""
Traffic & Overview routes -- first real (non-mock) Phase 12 domain.

Single endpoint answering "what does our traffic look like": total
views, unique visitors, top pages, device/platform breakdown. All
sourced from the real pages table, cached via traffic_service.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.traffic import TrafficOverviewResponse
from app.services.traffic_service import get_traffic_overview

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/overview", response_model=TrafficOverviewResponse)
async def get_traffic_overview_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> TrafficOverviewResponse:
    return await get_traffic_overview()