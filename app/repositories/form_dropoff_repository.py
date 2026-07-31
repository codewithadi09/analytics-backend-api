"""
Form Field Drop-off repository -- per-field focus/completion/error
counts and average time-to-complete, scoped to form_id='cx_diagnostic'.

avg_time_seconds pairs each visitor's first focus with their first
completion of a field WITHIN THE SAME SESSION (anonymous_id +
context_session_id), not just the same visitor. anonymous_id persists
across sessions/days -- pairing only by visitor let a focus in one
session get matched to a completion a day later in a different
session, producing a nonsensical multi-hour "fill time" for a single
form field. Session-scoping fixes that at the source rather than
papering over it with an arbitrary outlier cutoff.

Field names are read from the data itself (via UNION across all three
field-event tables), not hardcoded to the four known fields
(name/email/phone/message) -- if the form ever changes, this adapts
without a code change.
"""

from dataclasses import dataclass
from datetime import date

from app.database.connection import get_connection

_FORM_ID = "cx_diagnostic"


@dataclass(frozen=True)
class FieldDropoffRow:
    field_name: str
    focus_count: int
    complete_count: int
    error_count: int
    avg_time_seconds: float | None


def _date_filter_clause(start_date: date | None, end_date: date | None) -> str:
    """
    Named-parameter version, matching conversion_repository.py's
    approach -- this query already uses %(form_id)s style params, so
    the date filter follows the same %(start_date)s / %(end_date)s
    style rather than mixing in positional %s.
    """
    conditions = []
    if start_date is not None:
        conditions.append("timestamp >= %(start_date)s")
    if end_date is not None:
        conditions.append("timestamp < %(end_date)s + interval '1 day'")

    if not conditions:
        return ""
    return "AND " + " AND ".join(conditions)


async def get_field_dropoff_stats(
    start_date: date | None = None, end_date: date | None = None
) -> list[FieldDropoffRow]:
    """
    The date clause is applied everywhere timestamp is filterable:
    each of the three field_names UNION branches, each of the three
    count CTEs, and both first_focus/first_complete CTEs -- so a
    date-scoped query only considers focus/complete/error events that
    themselves happened in that window, not just filters the final
    aggregate.
    """
    clause = _date_filter_clause(start_date, end_date)
    params: dict = {"form_id": _FORM_ID}
    if start_date is not None:
        params["start_date"] = start_date
    if end_date is not None:
        params["end_date"] = end_date

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                WITH field_names AS (
                    SELECT field_name FROM rudder_schema.form_field_focus WHERE form_id = %(form_id)s {clause}
                    UNION
                    SELECT field_name FROM rudder_schema.form_field_complete WHERE form_id = %(form_id)s {clause}
                    UNION
                    SELECT field_name FROM rudder_schema.form_field_error WHERE form_id = %(form_id)s {clause}
                ),
                focus_counts AS (
                    SELECT field_name, COUNT(DISTINCT anonymous_id) AS focus_count
                    FROM rudder_schema.form_field_focus
                    WHERE form_id = %(form_id)s {clause}
                    GROUP BY field_name
                ),
                complete_counts AS (
                    SELECT field_name, COUNT(DISTINCT anonymous_id) AS complete_count
                    FROM rudder_schema.form_field_complete
                    WHERE form_id = %(form_id)s {clause}
                    GROUP BY field_name
                ),
                error_counts AS (
                    SELECT field_name, COUNT(DISTINCT anonymous_id) AS error_count
                    FROM rudder_schema.form_field_error
                    WHERE form_id = %(form_id)s {clause}
                    GROUP BY field_name
                ),
                first_focus AS (
                    SELECT DISTINCT ON (anonymous_id, context_session_id, field_name)
                        anonymous_id, context_session_id, field_name, timestamp AS focus_ts
                    FROM rudder_schema.form_field_focus
                    WHERE form_id = %(form_id)s {clause}
                    ORDER BY anonymous_id, context_session_id, field_name, timestamp ASC
                ),
                first_complete AS (
                    SELECT DISTINCT ON (anonymous_id, context_session_id, field_name)
                        anonymous_id, context_session_id, field_name, timestamp AS complete_ts
                    FROM rudder_schema.form_field_complete
                    WHERE form_id = %(form_id)s {clause}
                    ORDER BY anonymous_id, context_session_id, field_name, timestamp ASC
                ),
                avg_times AS (
                    SELECT
                        ff.field_name,
                        AVG(EXTRACT(EPOCH FROM (fc.complete_ts - ff.focus_ts))) AS avg_time_seconds
                    FROM first_focus ff
                    JOIN first_complete fc
                        ON fc.anonymous_id = ff.anonymous_id
                        AND fc.context_session_id = ff.context_session_id
                        AND fc.field_name = ff.field_name
                    WHERE fc.complete_ts >= ff.focus_ts
                    GROUP BY ff.field_name
                )
                SELECT
                    fn.field_name,
                    COALESCE(f.focus_count, 0),
                    COALESCE(c.complete_count, 0),
                    COALESCE(e.error_count, 0),
                    a.avg_time_seconds
                FROM field_names fn
                LEFT JOIN focus_counts f ON f.field_name = fn.field_name
                LEFT JOIN complete_counts c ON c.field_name = fn.field_name
                LEFT JOIN error_counts e ON e.field_name = fn.field_name
                LEFT JOIN avg_times a ON a.field_name = fn.field_name
                ORDER BY fn.field_name
                """,
                params,
            )
            rows = await cur.fetchall()
            return [
                FieldDropoffRow(
                    field_name=r[0],
                    focus_count=r[1],
                    complete_count=r[2],
                    error_count=r[3],
                    avg_time_seconds=round(float(r[4]), 2) if r[4] is not None else None,
                )
                for r in rows
            ]