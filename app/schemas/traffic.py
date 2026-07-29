"""
Request/response schemas for the Traffic & Overview endpoint.

Source table: pages (real RudderStack page-view records). See
app/repositories/traffic_repository.py for the query this backs.
"""

from pydantic import BaseModel, Field


class TopPage(BaseModel):
    """One page in the top-pages-by-traffic ranking."""

    path: str
    title: str | None = None
    views: int = Field(ge=0)


class DeviceBreakdown(BaseModel):
    """Visitor count split by mobile vs. desktop, from Client Hints data."""

    mobile: int = Field(ge=0)
    desktop: int = Field(ge=0)
    unknown: int = Field(
        ge=0,
        description="Requests where context_ua_ch_mobile was null -- "
        "older browsers without Client Hints support.",
    )


class PlatformBreakdown(BaseModel):
    """One OS/platform and its share of page views."""

    platform: str
    views: int = Field(ge=0)


class TrafficOverviewResponse(BaseModel):
    """Response body for GET /traffic/overview."""

    total_page_views: int = Field(ge=0)
    unique_visitors: int = Field(ge=0)
    top_pages: list[TopPage]
    device_breakdown: DeviceBreakdown
    platform_breakdown: list[PlatformBreakdown]