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

from app.database.connection import get_connection

_FORM_ID = "cx_diagnostic"


@dataclass(frozen=True)
class FunnelStepCountRow:
    step_name: str
    users: int


async def get_funnel_step_counts() -> list[FunnelStepCountRow]:
    """
    Distinct visitor count at each real funnel step, in fixed
    (non-sortable) step order.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 AS step_order, 'contact_us_page_view' AS step_name,
                       COUNT(DISTINCT anonymous_id) AS users
                FROM rudder_schema.pages
                WHERE path = '/contact-us'

                UNION ALL

                SELECT 2, 'form_start', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_start
                WHERE form_id = %(form_id)s

                UNION ALL

                SELECT 3, 'form_field_complete', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_field_complete
                WHERE form_id = %(form_id)s

                UNION ALL

                SELECT 4, 'form_submit', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_submit
                WHERE form_id = %(form_id)s

                UNION ALL

                SELECT 5, 'form_submit_success', COUNT(DISTINCT anonymous_id)
                FROM rudder_schema.form_submit_success
                WHERE form_id = %(form_id)s

                ORDER BY step_order
                """,
                {"form_id": _FORM_ID},
            )
            rows = await cur.fetchall()
            return [FunnelStepCountRow(step_name=r[1], users=r[2]) for r in rows]