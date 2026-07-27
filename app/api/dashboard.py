"""
Dashboard overview routes -- KPIs and conversion funnel.

Every route here requires a valid bearer token (see
app/auth/dependencies.py). This is the reference pattern every
other domain (funnel, retention, user_journey, users, filters)
will follow: route -> service -> repository.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.dashboard import FunnelResponse, KpiSummary
from app.services.dashboard_service import get_funnel, get_kpi_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=KpiSummary)
async def get_kpis_route(
    current_user: CurrentUser = Depends(get_current_user),
) -> KpiSummary:
    return await get_kpi_summary()


@router.get("/funnel", response_model=FunnelResponse)
async def get_funnel_route(
    current_user: CurrentUser = Depends(get_current_user),
) -> FunnelResponse:
    return await get_funnel()