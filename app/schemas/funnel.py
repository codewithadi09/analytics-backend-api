"""
Request/response schemas for funnel intelligence endpoints.
"""

from pydantic import BaseModel, Field


class SourceAttribution(BaseModel):
    """One traffic source's identity-resolved conversion performance."""

    source: str
    total_users: int = Field(ge=0)
    converters: int = Field(ge=0)
    conversion_rate_pct: float = Field(ge=0, le=100)


class SourceAttributionResponse(BaseModel):
    sources: list[SourceAttribution]


class ContentInfluence(BaseModel):
    """One page's conversion influence."""

    page_path: str
    total_visitors: int = Field(ge=0)
    converters: int = Field(ge=0)
    conversion_rate_pct: float = Field(ge=0, le=100)


class ContentInfluenceResponse(BaseModel):
    pages: list[ContentInfluence]


class CohortStats(BaseModel):
    """Behavioral averages for one cohort (converted / did not convert)."""

    cohort: str
    avg_events: float = Field(ge=0)
    avg_pages_visited: float = Field(ge=0)


class CohortComparisonResponse(BaseModel):
    cohorts: list[CohortStats]


class DropoffTimingBucket(BaseModel):
    """Non-converting users dropping off at a given hour of day (UTC)."""

    hour_of_day: int = Field(ge=0, le=23)
    users_dropping_off: int = Field(ge=0)
    dropoff_events: int = Field(ge=0)


class DropoffTimingResponse(BaseModel):
    buckets: list[DropoffTimingBucket]