"""
Services & Content Engagement routes -- page-level scroll depth and
engagement milestones, plus blog/case-study click engagement. All
real data from scroll_depth, page_engaged, blog_click, case_study_click,
and pages.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.engagement import ServicesContentEngagementResponse
from app.services.engagement_service import get_engagement_overview

router = APIRouter(prefix="/engagement", tags=["engagement"])


@router.get("/overview", response_model=ServicesContentEngagementResponse)
async def get_engagement_overview_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> ServicesContentEngagementResponse:
    return await get_engagement_overview()