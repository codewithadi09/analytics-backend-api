"""
Funnel intelligence routes -- source attribution, content influence,
cohort comparison, and dropoff timing.

All routes require a valid bearer token.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.funnel import (
    CohortComparisonResponse,
    ContentInfluenceResponse,
    DropoffTimingResponse,
    SourceAttributionResponse,
)
from app.services.funnel_service import (
    get_cohort_comparison_summary,
    get_content_influence_summary,
    get_dropoff_timing_summary,
    get_source_attribution_summary,
)

router = APIRouter(prefix="/funnel", tags=["funnel"])


@router.get("/source-attribution", response_model=SourceAttributionResponse)
async def get_source_attribution_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> SourceAttributionResponse:
    return await get_source_attribution_summary()


@router.get("/content-influence", response_model=ContentInfluenceResponse)
async def get_content_influence_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> ContentInfluenceResponse:
    return await get_content_influence_summary()


@router.get("/cohort-comparison", response_model=CohortComparisonResponse)
async def get_cohort_comparison_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> CohortComparisonResponse:
    return await get_cohort_comparison_summary()


@router.get("/dropoff-timing", response_model=DropoffTimingResponse)
async def get_dropoff_timing_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> DropoffTimingResponse:
    return await get_dropoff_timing_summary()