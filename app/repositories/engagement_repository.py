"""
Services & Content Engagement repository.

Reuses page-view counting from Domain 1 (pages) and click counting
from Domain 2 (blog_click, case_study_click), joined with two sources
not queried by any prior domain: scroll_depth.depth_percentage and
page_engaged.engagement_time. Both use their own page_path column
(confirmed present on both tables), not context_page_path.

Median scroll depth uses PERCENTILE_CONT -- more robust than average
alone on low-traffic pages where one outlier visitor can skew a mean.
"""

from dataclasses import dataclass

from app.database.connection import get_connection


@dataclass(frozen=True)
class PageEngagementRow:
    path: str
    views: int
    avg_scroll_depth_pct: float
    median_scroll_depth_pct: float
    engaged_visit_count: int


@dataclass(frozen=True)
class MilestoneBucketRow:
    milestone_seconds: int
    visit_count: int


@dataclass(frozen=True)
class ContentEngagementRow:
    content_type: str
    label: str
    url: str | None
    clicks: int


async def get_page_engagement() -> list[PageEngagementRow]:
    """
    Per-page views (from pages), average+median scroll depth (from
    scroll_depth), and engaged-visit count (from page_engaged).

    page_engaged fires repeatedly per visit -- once per milestone
    crossed (30s, 60s, 120s...), confirmed by the milestone breakdown
    showing many more 30s rows than 180s rows for the same traffic.
    A raw COUNT(*) would count milestone EVENTS, not engaged VISITS,
    and could exceed the page's own view count. COUNT(DISTINCT ...)
    on (anonymous_id, context_session_id, page_path) collapses all of
    one visit's milestone rows down to a single engaged visit.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                WITH view_counts AS (
                    SELECT path, COUNT(*) AS views
                    FROM rudder_schema.pages
                    WHERE path IS NOT NULL
                    GROUP BY path
                ),
                scroll_stats AS (
                    SELECT
                        page_path,
                        AVG(depth_percentage) AS avg_depth,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY depth_percentage) AS median_depth
                    FROM rudder_schema.scroll_depth
                    WHERE page_path IS NOT NULL
                    GROUP BY page_path
                ),
                engaged_counts AS (
                    SELECT
                        page_path,
                        COUNT(DISTINCT (anonymous_id, context_session_id)) AS engaged_visits
                    FROM rudder_schema.page_engaged
                    WHERE page_path IS NOT NULL
                    GROUP BY page_path
                )
                SELECT
                    v.path,
                    v.views,
                    COALESCE(s.avg_depth, 0),
                    COALESCE(s.median_depth, 0),
                    COALESCE(e.engaged_visits, 0)
                FROM view_counts v
                LEFT JOIN scroll_stats s ON s.page_path = v.path
                LEFT JOIN engaged_counts e ON e.page_path = v.path
                ORDER BY v.views DESC
                """
            )
            rows = await cur.fetchall()
            return [
                PageEngagementRow(
                    path=r[0],
                    views=r[1],
                    avg_scroll_depth_pct=round(float(r[2]), 2),
                    median_scroll_depth_pct=round(float(r[3]), 2),
                    engaged_visit_count=r[4],
                )
                for r in rows
            ]


async def get_milestone_breakdown() -> list[MilestoneBucketRow]:
    """Site-wide count of visits per engagement_time bucket (30/60/120/180)."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT engagement_time, COUNT(*) AS visit_count
                FROM rudder_schema.page_engaged
                WHERE engagement_time IS NOT NULL
                GROUP BY engagement_time
                ORDER BY engagement_time ASC
                """
            )
            rows = await cur.fetchall()
            return [MilestoneBucketRow(milestone_seconds=r[0], visit_count=r[1]) for r in rows]


async def get_content_engagement() -> list[ContentEngagementRow]:
    """Blog and case-study click counts, grouped by the specific content item."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 'blog' AS content_type, blog_title AS label, blog_url AS url, COUNT(*) AS clicks
                FROM rudder_schema.blog_click
                WHERE blog_title IS NOT NULL
                GROUP BY blog_title, blog_url
                UNION ALL
                SELECT 'case_study', case_study_title, case_study_url, COUNT(*)
                FROM rudder_schema.case_study_click
                WHERE case_study_title IS NOT NULL
                GROUP BY case_study_title, case_study_url
                ORDER BY clicks DESC
                """
            )
            rows = await cur.fetchall()
            return [
                ContentEngagementRow(content_type=r[0], label=r[1], url=r[2], clicks=r[3])
                for r in rows
            ]