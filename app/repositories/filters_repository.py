"""
Filters repository -- currently backed by mock data for the parts
that will eventually come from real event data (date range, traffic
sources). Funnel steps and event names are NOT mocked here since
they're already static, single-source-of-truth constants in
app/core/constants.py -- duplicating them as "mock data" would just
create a second place they could drift out of sync.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DateRangeRow:
    earliest_event: str
    latest_event: str


_MOCK_TRAFFIC_SOURCES = ["google", "direct", "facebook", "newsletter", "twitter"]

_MOCK_DATE_RANGE = DateRangeRow(
    earliest_event="2026-01-05",
    latest_event="2026-07-27",
)


async def get_traffic_sources() -> list[str]:
    """
    Phase 12 replacement: SELECT DISTINCT source FROM events
    WHERE source IS NOT NULL ORDER BY source.
    """
    return _MOCK_TRAFFIC_SOURCES


async def get_date_range() -> DateRangeRow:
    """
    Phase 12 replacement: SELECT MIN(event_timestamp), MAX(event_timestamp)
    FROM events.
    """
    return _MOCK_DATE_RANGE