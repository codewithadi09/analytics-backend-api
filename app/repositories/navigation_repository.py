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
from datetime import date

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


def _date_filter_clause(
    start_date: date | None, end_date: date | None, prefix: str = "AND"
) -> tuple[str, list]:
    """Same pattern as traffic/interactions repositories."""
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


async def get_total_sessions(
    start_date: date | None = None, end_date: date | None = None
) -> int:
    """Total distinct (anonymous_id, context_session_id) sessions."""
    clause, params = _date_filter_clause(start_date, end_date, prefix="AND")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT anonymous_id, context_session_id
                    FROM rudder_schema.pages
                    WHERE context_session_id IS NOT NULL {clause}
                ) sessions
                """,
                params,
            )
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_top_navigation_paths(
    limit: int = 10,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[NavigationPathRow]:
    """
    Most common navigation paths, ranked by session count. Collapses
    consecutive duplicate pages within a session before building the
    path sequence.
    """
    clause, date_params = _date_filter_clause(start_date, end_date, prefix="AND")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
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
                    WHERE context_session_id IS NOT NULL AND path IS NOT NULL {clause}
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
                (*date_params, limit),
            )
            rows = await cur.fetchall()
            return [NavigationPathRow(steps=r[0], session_count=r[1]) for r in rows]


async def get_average_pages_per_session(
    start_date: date | None = None, end_date: date | None = None
) -> float:
    """Average raw page-view count per session (not deduplicated -- total views, not steps)."""
    clause, params = _date_filter_clause(start_date, end_date, prefix="AND")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT AVG(page_count) FROM (
                    SELECT anonymous_id, context_session_id, COUNT(*) AS page_count
                    FROM rudder_schema.pages
                    WHERE context_session_id IS NOT NULL {clause}
                    GROUP BY anonymous_id, context_session_id
                ) sub
                """,
                params,
            )
            row = await cur.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0


async def get_exit_rates(
    start_date: date | None = None, end_date: date | None = None
) -> list[ExitRateRow]:
    """
    Exit rate per page -- how often each page was the LAST page
    visited in a session. Uses DISTINCT ON to pick each session's
    final page efficiently (one row per session, chosen by latest
    timestamp), then groups by page.
    """
    clause, params = _date_filter_clause(start_date, end_date, prefix="AND")
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                WITH last_pages AS (
                    SELECT DISTINCT ON (anonymous_id, context_session_id)
                        anonymous_id, context_session_id, path
                    FROM rudder_schema.pages
                    WHERE context_session_id IS NOT NULL AND path IS NOT NULL {clause}
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
                """,
                params,
            )
            rows = await cur.fetchall()
            return [
                ExitRateRow(path=r[0], exits=r[1], exit_rate_pct=float(r[2]))
                for r in rows
            ]