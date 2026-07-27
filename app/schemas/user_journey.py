"""
Request/response schemas for user journey endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class IdentifiedUser(BaseModel):
    """One row in the searchable/browsable user list."""

    user_id: str  # email, matching how the Streamlit page keys users
    user_name: str


class UserCounts(BaseModel):
    """Dataset-wide user counts shown while no user is selected."""

    total_identified_users: int = Field(ge=0)
    total_users: int = Field(ge=0)
    anonymous_users: int = Field(ge=0)


class JourneyEvent(BaseModel):
    """One event in a user's timeline, in chronological order."""

    event_name: str
    event_timestamp: str  # ISO 8601 string
    detail: str = Field(
        default="",
        description="Human-readable context for the event -- product name, "
        "page path, order id, etc., depending on event_name.",
    )


class UserJourneyResponse(BaseModel):
    """Full journey for a single user, plus summary stats."""

    user_id: str
    user_name: str
    total_events: int = Field(ge=0)
    session_duration_minutes: int = Field(ge=0)
    unique_pages: int = Field(ge=0)
    has_purchased: bool
    has_signed_up: bool
    events: list[JourneyEvent]