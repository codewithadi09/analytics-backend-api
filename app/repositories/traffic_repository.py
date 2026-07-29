"""
Traffic & Overview repository -- real SQL against the pages table.

First Phase 12 domain built against actual RudderStack data
(rudder_schema.pages), replacing the old Phase 5 mock dashboard
repository. Raw parameterized SQL via psycopg3, no ORM -- consistent
with every other repository in this project.
"""

from dataclasses import dataclass

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


async def get_total_page_views() -> int:
    """Total row count in pages -- every page load ever recorded."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM rudder_schema.pages")
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_unique_visitors() -> int:
    """Distinct anonymous_id count -- our reliable unique-visitor key."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(DISTINCT anonymous_id) FROM rudder_schema.pages"
            )
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_top_pages(limit: int = 10) -> list[TopPageRow]:
    """Most-visited pages by raw view count, grouped by path."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT path, MAX(title) AS title, COUNT(*) AS views
                FROM rudder_schema.pages
                WHERE path IS NOT NULL
                GROUP BY path
                ORDER BY views DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = await cur.fetchall()
            return [TopPageRow(path=r[0], title=r[1], views=r[2]) for r in rows]


async def get_device_breakdown() -> DeviceBreakdownRow:
    """
    Mobile vs desktop split from context_ua_ch_mobile. NULL means the
    visitor's browser didn't send Client Hints (e.g. Safari) -- kept
    as an explicit 'unknown' bucket rather than dropped or guessed.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE context_ua_ch_mobile IS TRUE) AS mobile,
                    COUNT(*) FILTER (WHERE context_ua_ch_mobile IS FALSE) AS desktop,
                    COUNT(*) FILTER (WHERE context_ua_ch_mobile IS NULL) AS unknown
                FROM rudder_schema.pages
                """
            )
            row = await cur.fetchone()
            return DeviceBreakdownRow(mobile=row[0], desktop=row[1], unknown=row[2])


async def get_platform_breakdown() -> list[PlatformBreakdownRow]:
    """
    View counts grouped by OS/platform. Rows with a null platform are
    excluded -- same Client Hints gap as the device breakdown above.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT context_ua_ch_platform, COUNT(*) AS views
                FROM rudder_schema.pages
                WHERE context_ua_ch_platform IS NOT NULL
                GROUP BY context_ua_ch_platform
                ORDER BY views DESC
                """
            )
            rows = await cur.fetchall()
            return [PlatformBreakdownRow(platform=r[0], views=r[1]) for r in rows]