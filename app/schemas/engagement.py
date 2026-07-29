"""
Request/response schemas for the Services & Content Engagement domain.

Reuses concepts from Domain 1 (page views) and Domain 2 (click counts)
scoped to services/sub-services/blog/case-study content, plus two data
sources not queried by any prior domain: scroll_depth.depth_percentage
and page_engaged.engagement_time.

engagement_time is a confirmed bucketed milestone value (only ever
30/60/120/180), not a continuous duration -- reported as counts per
bucket, not averaged, since averaging a discrete/bucketed value
produces a technically-computable but meaningless number.
"""

from pydantic import BaseModel, Field


class PageEngagement(BaseModel):
    """One page's traffic + attention signals -- 'gets traffic but no attention' check."""

    path: str
    views: int = Field(ge=0)
    avg_scroll_depth_pct: float = Field(ge=0, le=100)
    median_scroll_depth_pct: float = Field(ge=0, le=100)
    engaged_visit_count: int = Field(
        ge=0, description="Visits where ANY engagement milestone fired."
    )


class EngagementMilestoneBucket(BaseModel):
    """One engagement_time bucket (30/60/120/180 seconds) and how many visits hit it."""

    milestone_seconds: int
    visit_count: int = Field(ge=0)


class ContentEngagementItem(BaseModel):
    """One blog post or case study and its click-engagement count."""

    content_type: str = Field(description="'blog' or 'case_study'.")
    label: str
    url: str | None = None
    clicks: int = Field(ge=0)


class ServicesContentEngagementResponse(BaseModel):
    """Response body for GET /engagement/overview."""

    page_engagement: list[PageEngagement]
    milestone_breakdown: list[EngagementMilestoneBucket]
    content_engagement: list[ContentEngagementItem]