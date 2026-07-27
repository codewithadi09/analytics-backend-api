"""
Request/response schemas for the dashboard overview endpoints.
"""

from pydantic import BaseModel, Field


class KpiSummary(BaseModel):
    """Response body for GET /dashboard/kpis."""

    total_users: int = Field(ge=0)
    total_orders: int = Field(ge=0)
    total_revenue: float = Field(ge=0)
    avg_order_value: float = Field(ge=0)
    total_signups: int = Field(ge=0)
    total_form_submissions: int = Field(ge=0)


class FunnelStep(BaseModel):
    """One row in the conversion funnel."""

    event_name: str
    users: int = Field(ge=0)
    dropoff_pct: float = Field(
        ge=0, le=100, description="Percent drop from the previous step"
    )
    conversion_from_top: float = Field(
        ge=0, le=100, description="Percent of the very first step this step represents"
    )


class FunnelResponse(BaseModel):
    """Response body for GET /dashboard/funnel."""

    steps: list[FunnelStep]