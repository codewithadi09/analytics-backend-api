"""
Form Field Drop-off routes -- which specific cx_diagnostic form field
causes the most abandonment, and how long each field takes to fill.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_rate_limit
from app.schemas.auth import CurrentUser
from app.schemas.form_dropoff import FormFieldDropoffResponse
from app.services.form_dropoff_service import get_form_dropoff_overview

router = APIRouter(prefix="/form-dropoff", tags=["form-dropoff"])


@router.get("/overview", response_model=FormFieldDropoffResponse)
async def get_form_dropoff_overview_route(
    current_user: CurrentUser = Depends(require_rate_limit),
) -> FormFieldDropoffResponse:
    return await get_form_dropoff_overview()