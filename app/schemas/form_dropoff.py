"""
Request/response schemas for the Form Field Drop-off domain.

Per-field abandonment within the cx_diagnostic form (fields: name,
email, phone, message -- confirmed in the handoff doc). Distinct from
Domain 6's Conversion Funnel: that domain answers "how many people
converted overall"; this one answers "which specific field causes
people to give up," using form_field_focus/complete/error timestamp
deltas.

avg_time_seconds is computed by pairing each visitor's focus timestamp
with their complete timestamp for the same field -- see
app/repositories/form_dropoff_repository.py for how visitors who never
completed a field are excluded from that specific average (they have
no completion timestamp to pair against).
"""

from pydantic import BaseModel, Field


class FieldDropoff(BaseModel):
    """One form field's engagement and abandonment signals."""

    field_name: str
    focus_count: int = Field(ge=0, description="Distinct visitors who focused this field.")
    complete_count: int = Field(ge=0, description="Distinct visitors who completed this field.")
    error_count: int = Field(ge=0, description="Distinct visitors who hit a validation error on this field.")
    dropoff_pct: float = Field(
        ge=0, le=100, description="Percent of visitors who focused but never completed this field."
    )
    avg_time_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Average seconds between focus and completion, for visitors "
        "who did complete this field. Null if no completions exist yet to average.",
    )


class FormFieldDropoffResponse(BaseModel):
    """Response body for GET /form-dropoff/overview."""

    fields: list[FieldDropoff]
    most_common_dropoff_field: str | None = Field(
        default=None,
        description="The field with the highest raw dropoff count -- where most "
        "visitors are actually giving up, not just the highest percentage.",
    )