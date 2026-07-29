"""
Navigation Path Analysis repository -- reconstructs per-visitor page
sequences from the pages table, ordered by timestamp within each real
RudderStack session (anonymous_id + context_session_id).

Consecutive duplicate pages within a session are collapsed before
building a path (a reload/back-button bounce isn't a real navigation
step). visitor_count in the output is really "session count" -- a
repeat visitor with two sessions following the same path counts
twice. See app/services/navigation_service.py docstring for why this
tradeoff is acceptable for now.
"""

from dataclasses import dataclass

from app.database.connection import get_connection


@dataclass(frozen=True)
class NavigationPathRow:
    steps: list[str]
    session_count: int


@dataclass(frozen=True)
class ExitRateRow:
    path: str
    exits: int
    exit_rate_pct: float


async def get_total_sessions() -> int:
    """Total distinct (anonymous_id, context_session_id) sessions."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT anonymous_id, context_session_id
                    FROM rudder_schema.pages
                    WHERE context_session_id IS NOT NULL
                ) sessions
                """
            )
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_top_navigation_paths(limit: int = 10) -> list[NavigationPathRow]:
    """
    Most common navigation paths, ranked by session count. Collapses
    consecutive duplicate pages within a session before building the
    path sequence.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                WITH ordered_pages AS (
                    SELECT
                        anonymous_id,
                        context_session_id,
                        path,
                        timestamp,
                        LAG(path) OVER (
                            PARTITION BY anonymous_id, context_session_id
                            ORDER BY timestamp
                        ) AS prev_path
                    FROM rudder_schema.pages
                    WHERE context_session_id IS NOT NULL AND path IS NOT NULL
                ),
                deduped AS (
                    SELECT anonymous_id, context_session_id, path, timestamp
                    FROM ordered_pages
                    WHERE prev_path IS DISTINCT FROM path
                ),
                session_sequences AS (
                    SELECT
                        anonymous_id,
                        context_session_id,
                        array_agg(path ORDER BY timestamp) AS path_sequence
                    FROM deduped
                    GROUP BY anonymous_id, context_session_id
                )
                SELECT path_sequence, COUNT(*) AS session_count
                FROM session_sequences
                GROUP BY path_sequence
                ORDER BY session_count DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = await cur.fetchall()
            return [NavigationPathRow(steps=r[0], session_count=r[1]) for r in rows]


async def get_average_pages_per_session() -> float:
    """Average raw page-view count per session (not deduplicated -- total views, not steps)."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT AVG(page_count) FROM (
                    SELECT anonymous_id, context_session_id, COUNT(*) AS page_count
                    FROM rudder_schema.pages
                    WHERE context_session_id IS NOT NULL
                    GROUP BY anonymous_id, context_session_id
                ) sub
                """
            )
            row = await cur.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0


async def get_exit_rates() -> list[ExitRateRow]:
    """
    Exit rate per page -- how often each page was the LAST page
    visited in a session. Uses DISTINCT ON to pick each session's
    final page efficiently (one row per session, chosen by latest
    timestamp), then groups by page.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                WITH last_pages AS (
                    SELECT DISTINCT ON (anonymous_id, context_session_id)
                        anonymous_id, context_session_id, path
                    FROM rudder_schema.pages
                    WHERE context_session_id IS NOT NULL AND path IS NOT NULL
                    ORDER BY anonymous_id, context_session_id, timestamp DESC
                ),
                total AS (
                    SELECT COUNT(*) AS total_sessions FROM last_pages
                )
                SELECT
                    path,
                    COUNT(*) AS exits,
                    ROUND(COUNT(*) * 100.0 / (SELECT total_sessions FROM total), 2) AS exit_rate_pct
                FROM last_pages
                GROUP BY path
                ORDER BY exits DESC
                """
            )
            rows = await cur.fetchall()
            return [
                ExitRateRow(path=r[0], exits=r[1], exit_rate_pct=float(r[2]))
                for r in rows
            ]