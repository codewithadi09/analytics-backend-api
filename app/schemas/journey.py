"""
Request/response schemas for the User Journey (cross-session) domain.

Looked up by anonymous_id -- the reliable, always-present identity
key confirmed in the handoff doc, rather than an email/user_id that
only exists post-conversion. Spans pages + all 16 click tables + the
form funnel, unioned and ordered chronologically, deliberately NOT
reset at session boundaries (that's what makes this "cross-session,"
distinct from Domain 3's per-session path analysis).
"""

from pydantic import BaseModel, EmailStr, Field


class ResolvedIdentity(BaseModel):
    """Email/name from `identifies`, populated only if this visitor has converted."""

    email: EmailStr | None = None
    name: str | None = None


class JourneyEvent(BaseModel):
    """One event in a visitor's full chronological timeline, regardless of source table."""

    event_category: str = Field(
        description="One of: 'page_view', 'click', 'form_activity' -- lets the "
        "frontend group the timeline without string-matching event_type itself."
    )
    event_type: str = Field(
        description="The specific source, e.g. 'page_view', 'cta_click', 'form_submit_success'."
    )
    label: str | None = None
    page_path: str | None = None
    timestamp: str  # ISO 8601 string


class UserJourneyResponse(BaseModel):
    """Response body for GET /journey/{anonymous_id}."""

    anonymous_id: str
    resolved_identity: ResolvedIdentity | None = None
    total_events: int = Field(ge=0)
    session_count: int = Field(ge=0)
    first_seen: str  # ISO 8601 string
    last_seen: str  # ISO 8601 string
    has_converted: bool
    events: list[JourneyEvent]

class VisitorSummary(BaseModel):
    """One row in the visitor selector list -- GET /journey/visitors."""

    anonymous_id: str
    email: EmailStr | None = None
    name: str | None = None
    first_seen: str  # ISO 8601 string
    last_seen: str  # ISO 8601 string