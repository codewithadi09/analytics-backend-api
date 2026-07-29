"""
Request/response schemas for the Conversion Funnel (real) domain.

The core metric per the project owner. Steps: /contact-us page view
-> form_start -> form_field_complete (at least one field) ->
form_submit -> form_submit_success, scoped to form_id = 'cx_diagnostic'
(the only form on the site).

form_submit_success is the real conversion signal -- confirmed via
direct DB querying against an internal reference doc that incorrectly
proposed form_start as a conversion proxy. Getting this step right is
the entire point of this domain; see repository module docstring for
the full reasoning.

form_field_focus and form_field_error are deliberately excluded as
funnel steps -- focus doesn't represent forward progress (can repeat
per field), and errors are a quality signal (Domain 7's job), not a
funnel stage.
"""

from pydantic import BaseModel, Field


class ConversionFunnelStep(BaseModel):
    """One stage in the real lead-generation funnel."""

    step_name: str
    users: int = Field(ge=0, description="Distinct anonymous_id count reaching this step.")
    dropoff_pct: float = Field(ge=0, le=100, description="Percent drop from the previous step.")
    conversion_from_top: float = Field(
        ge=0, le=100, description="Percent of the very first step this step represents."
    )


class ConversionFunnelResponse(BaseModel):
    """Response body for GET /conversion/funnel."""

    steps: list[ConversionFunnelStep]