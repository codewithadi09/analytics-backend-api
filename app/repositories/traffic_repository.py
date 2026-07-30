"""
Traffic & Overview repository -- real SQL against the pages table.

First Phase 12 domain built against actual RudderStack data
(rudder_schema.pages), replacing the old Phase 5 mock dashboard
repository. Raw parameterized SQL via psycopg3, no ORM -- consistent
with every other repository in this project.
"""

from dataclasses import dataclass
from datetime import date

from app.database.connection import get_connection


@dataclass(frozen=True)
class TopPageRow:
    path: str
    title: str | None
    views: int


@dataclass(frozen=True)
class PlatformBreakdownRow:
    platform: str
    views: int


@dataclass(frozen=True)
class DeviceBreakdownRow:
    mobile: int
    desktop: int
    unknown: int


def _date_filter_clause(
    start_date: date | None, end_date: date | None, prefix: str = "WHERE"
) -> tuple[str, list]:
    """
    Builds a SQL fragment and matching parameter list for an optional
    date range filter on the `timestamp` column.

    start_date is inclusive from midnight; end_date is inclusive
    through the very end of that day (hence the '+ interval 1 day'
    upper bound, rather than a plain <=, which would silently cut off
    that whole final day since timestamp is a full datetime, not a
    bare date).

    `prefix` lets callers reuse this when they already have a WHERE
    clause (pass "AND") vs when they don't (pass "WHERE").
    """
    conditions = []
    params: list = []

    if start_date is not None:
        conditions.append("timestamp >= %s")
        params.append(start_date)
    if end_date is not None:
        conditions.append("timestamp < %s + interval '1 day'")
        params.append(end_date)

    if not conditions:
        return "", []

    joiner = " AND ".join(conditions)
    return f"{prefix} {joiner}", params


async def get_total_page_views(
    start_date: date | None = None, end_date: date | None = None
) -> int:
    """Total row count in pages -- every page load ever recorded."""
    clause, params = _date_filter_clause(start_date, end_date, prefix="WHERE")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"SELECT COUNT(*) FROM rudder_schema.pages {clause}", params
            )
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_unique_visitors(
    start_date: date | None = None, end_date: date | None = None
) -> int:
    """Distinct anonymous_id count -- our reliable unique-visitor key."""
    clause, params = _date_filter_clause(start_date, end_date, prefix="WHERE")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT COUNT(DISTINCT anonymous_id) FROM rudder_schema.pages {clause}
                """,
                params,
            )
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_top_pages(
    limit: int = 10,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[TopPageRow]:
    """Most-visited pages by raw view count, grouped by path."""
    date_clause, date_params = _date_filter_clause(start_date, end_date, prefix="AND")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT path, MAX(title) AS title, COUNT(*) AS views
                FROM rudder_schema.pages
                WHERE path IS NOT NULL {date_clause}
                GROUP BY path
                ORDER BY views DESC
                LIMIT %s
                """,
                (*date_params, limit),
            )
            rows = await cur.fetchall()
            return [TopPageRow(path=r[0], title=r[1], views=r[2]) for r in rows]


async def get_device_breakdown(
    start_date: date | None = None, end_date: date | None = None
) -> DeviceBreakdownRow:
    """
    Mobile vs desktop split from context_ua_ch_mobile. NULL means the
    visitor's browser didn't send Client Hints (e.g. Safari) -- kept
    as an explicit 'unknown' bucket rather than dropped or guessed.
    """
    clause, params = _date_filter_clause(start_date, end_date, prefix="WHERE")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT
                    COUNT(*) FILTER (WHERE context_ua_ch_mobile IS TRUE) AS mobile,
                    COUNT(*) FILTER (WHERE context_ua_ch_mobile IS FALSE) AS desktop,
                    COUNT(*) FILTER (WHERE context_ua_ch_mobile IS NULL) AS unknown
                FROM rudder_schema.pages
                {clause}
                """,
                params,
            )
            row = await cur.fetchone()
            return DeviceBreakdownRow(mobile=row[0], desktop=row[1], unknown=row[2])


async def get_platform_breakdown(
    start_date: date | None = None, end_date: date | None = None
) -> list[PlatformBreakdownRow]:
    """
    View counts grouped by OS/platform. Rows with a null platform are
    excluded -- same Client Hints gap as the device breakdown above.
    """
    date_clause, date_params = _date_filter_clause(start_date, end_date, prefix="AND")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT context_ua_ch_platform, COUNT(*) AS views
                FROM rudder_schema.pages
                WHERE context_ua_ch_platform IS NOT NULL {date_clause}
                GROUP BY context_ua_ch_platform
                ORDER BY views DESC
                """,
                date_params,
            )
            rows = await cur.fetchall()
            return [PlatformBreakdownRow(platform=r[0], views=r[1]) for r in rows]