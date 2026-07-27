"""
Funnel intelligence repository -- currently backed by mock data.

Per the layered-build plan, this is the ONLY file that changes in
Phase 12 when real PostgreSQL credentials are available.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceAttributionRow:
    source: str
    total_users: int
    converters: int


@dataclass(frozen=True)
class ContentInfluenceRow:
    page_path: str
    total_visitors: int
    converters: int


@dataclass(frozen=True)
class CohortStatsRow:
    cohort: str
    avg_events: float
    avg_pages_visited: float


@dataclass(frozen=True)
class DropoffTimingRow:
    hour_of_day: int
    users_dropping_off: int
    dropoff_events: int


async def get_source_attribution() -> list[SourceAttributionRow]:
    """
    Phase 12 replacement: identity-resolved first-touch attribution
    query, joining events -> resolved user id -> orders, grouped by
    first-touch source.
    """
    return [
        SourceAttributionRow(source="google", total_users=520, converters=88),
        SourceAttributionRow(source="direct", total_users=340, converters=41),
        SourceAttributionRow(source="facebook", total_users=210, converters=19),
        SourceAttributionRow(source="newsletter", total_users=95, converters=22),
        SourceAttributionRow(source="twitter", total_users=75, converters=6),
    ]


async def get_content_influence() -> list[ContentInfluenceRow]:
    """
    Phase 12 replacement: per-page visitor/converter counts, e.g.
        SELECT page_path, COUNT(DISTINCT user_id) AS total_visitors,
               COUNT(DISTINCT user_id) FILTER (WHERE converted) AS converters
        FROM page_views ...
    """
    return [
        ContentInfluenceRow(page_path="/", total_visitors=980, converters=120),
        ContentInfluenceRow(page_path="/pricing", total_visitors=410, converters=95),
        ContentInfluenceRow(page_path="/product/8f3a2b1c", total_visitors=260, converters=70),
        ContentInfluenceRow(page_path="/blog/getting-started", total_visitors=190, converters=12),
        ContentInfluenceRow(page_path="/product/1a9c7d4e", total_visitors=150, converters=38),
    ]


async def get_cohort_comparison() -> list[CohortStatsRow]:
    """
    Phase 12 replacement: average event count and distinct pages
    visited, grouped by whether the user ever completed an order.
    """
    return [
        CohortStatsRow(cohort="Converted", avg_events=18.4, avg_pages_visited=7.2),
        CohortStatsRow(cohort="Did Not Convert", avg_events=4.1, avg_pages_visited=2.3),
    ]


async def get_dropoff_timing() -> list[DropoffTimingRow]:
    """
    Phase 12 replacement: hour-of-day (UTC) bucketed count of users
    whose last event was NOT order_completed, i.e. they went dark
    without converting.
    """
    return [
        DropoffTimingRow(hour_of_day=h, users_dropping_off=users, dropoff_events=events)
        for h, users, events in [
            (0, 12, 18), (1, 8, 11), (2, 5, 7), (3, 4, 6), (4, 3, 4),
            (5, 6, 9), (6, 14, 20), (7, 22, 31), (8, 35, 48), (9, 41, 55),
            (10, 38, 50), (11, 44, 60), (12, 52, 70), (13, 48, 65),
            (14, 61, 82), (15, 55, 74), (16, 47, 63), (17, 40, 54),
            (18, 33, 45), (19, 29, 39), (20, 25, 34), (21, 20, 27),
            (22, 17, 23), (23, 14, 19),
        ]
    ]