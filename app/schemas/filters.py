"""
Request/response schemas for the filters endpoint.

This is UI-support infrastructure, not a dashboard visualization --
the frontend calls this once to populate dropdowns, date pickers,
and multi-select filters across every other dashboard page.
"""

from pydantic import BaseModel


class DateRange(BaseModel):
    earliest_event: str  # ISO 8601 date
    latest_event: str    # ISO 8601 date


class FilterOptionsResponse(BaseModel):
    funnel_steps: list[str]
    event_names: list[str]
    traffic_sources: list[str]
    date_range: DateRange