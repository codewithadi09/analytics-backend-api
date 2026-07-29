"""
Request/response schemas for the Drop-off Explorer domain.

The operational counterpart to Domain 6's Conversion Funnel: not "what
percentage dropped off between two stages" but "give me the specific,
followable visitors who hit stage one and never reached stage two."
from_step/to_step are validated against the real FUNNEL_STEPS list in
core/constants.py (Domain 6's actual funnel stages), not the old fake
e-commerce steps.
"""

from pydantic import BaseModel, Field


class DropoffVisitor(BaseModel):
    """One visitor who reached from_step but never reached to_step."""

    anonymous_id: str
    last_known_action: str = Field(
        description="The event_type of their most recent recorded activity."
    )
    last_seen: str  # ISO 8601 string


class DropoffSummary(BaseModel):
    """Summary counts for a chosen from_step/to_step pair."""

    from_step: str
    to_step: str
    total_dropoff: int = Field(ge=0)