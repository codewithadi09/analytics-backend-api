"""
Conversion Funnel (real) routes -- the core lead-generation metric,
per the project owner. Real steps (contact-us page view through
form_submit_success), replacing the old mock e-commerce funnel.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.conversion import ConversionFunnelResponse
from app.services.conversion_service import get_conversion_funnel

router = APIRouter(prefix="/conversion", tags=["conversion"])


@router.get("/funnel", response_model=ConversionFunnelResponse)
async def get_conversion_funnel_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> ConversionFunnelResponse:
    return await get_conversion_funnel()