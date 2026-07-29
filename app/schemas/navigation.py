"""
Request/response schemas for the Navigation Path Analysis domain.

Represents a "path" as an ordered list of page paths (not a
pre-joined "A -> B -> C" string) -- arrow-joining and display
formatting is a frontend concern, not part of the API contract.
"""

from pydantic import BaseModel, Field


class NavigationPath(BaseModel):
    """One common multi-step route through the site, ranked by frequency."""

    steps: list[str] = Field(
        description="Ordered page paths, e.g. ['/', '/services', '/contact-us']."
    )
    visitor_count: int = Field(ge=0)
    percentage: float = Field(
        ge=0, le=100, description="Percent of all visitors who followed this exact path."
    )


class ExitRateByPage(BaseModel):
    """One page's exit rate -- how often it was the last page in a visitor's session."""

    path: str
    exits: int = Field(ge=0)
    exit_rate_pct: float = Field(ge=0, le=100)


class NavigationOverviewResponse(BaseModel):
    """Response body for GET /navigation/overview."""

    top_paths: list[NavigationPath]
    average_pages_per_session: float = Field(ge=0)
    exit_rates: list[ExitRateByPage]