"""
Conversion Funnel (real) repository -- the core lead-generation metric.

Steps: /contact-us page view -> form_start -> form_field_complete ->
form_submit -> form_submit_success, all scoped to form_id =
'cx_diagnostic' (the only form on the entire site, confirmed via
direct SQL). form_submit_success is the true conversion signal --
confirmed via direct DB querying against an internal reference doc
that incorrectly proposed form_start as a proxy before form_submit
and form_submit_success were found to exist with real data. Getting
this step right is the entire point of this domain.

A fixed step_order tag preserves funnel sequence in the UNION ALL --
unlike Domain 2's leaderboard, step order here is meaningful and must
NOT be sorted by count.
"""

from dataclasses import dataclass
from datetime import date

from app.database.connection import get_connection

_FORM_ID = "cx_diagnostic"


@dataclass(frozen=True)
class FunnelStepCountRow:
    step_name: str
    users: int


def _date_filter_clause(start_date: date | None, end_date: date | None) -> str:
    """
    Named-parameter version of the same date filter helper used
    elsewhere -- this repository already uses %(form_id)s style
    params, and psycopg doesn't allow mixing named and positional
    placeholders in one query, so start_date/end_date use the same
    %(start_date)s / %(end_date)s style rather than %s.
    """
    conditions = []
    if start_date is not None:
        conditions.append("timestamp >= %(start_date)s")
    if end_date is not None:
        conditions.append("timestamp < %(end_date)s + interval '1 day'")

    if not conditions:
        return ""
    return "AND " + " AND ".join(conditions)


async def get_funnel_step_counts(
    start_date: date | None = None, end_date: date | None = None
) -> list[FunnelStepCountRow]:
    """
    Distinct visitor count at each real funnel step, in fixed
    (non-sortable) step order. The same date clause is applied inside
    every one of the five SELECTs -- each table has its own timestamp
    column, so filtering happens per-subquery, same as Interactions
    and Engagement's multi-table queries.
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
                SELECT 1 AS step_order, 'contact_us_page_view' AS step_name,
                       COUNT(DISTINCT anonymous_id) AS users
                FROM rudder_schema.pages
                WHERE path = '/contact-us' {clause}

                UNION ALL

                SELECT 2, 'form_start', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_start
                WHERE form_id = %(form_id)s {clause}

                UNION ALL

                SELECT 3, 'form_field_complete', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_field_complete
                WHERE form_id = %(form_id)s {clause}

                UNION ALL

                SELECT 4, 'form_submit', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_submit
                WHERE form_id = %(form_id)s {clause}

                UNION ALL

                SELECT 5, 'form_submit_success', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_submit_success
                WHERE form_id = %(form_id)s {clause}

                ORDER BY step_order
                """,
                params,
            )
            rows = await cur.fetchall()
            return [FunnelStepCountRow(step_name=r[1], users=r[2]) for r in rows]