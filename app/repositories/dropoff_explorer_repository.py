"""
Drop-off Explorer repository -- the operational counterpart to Domain
6's Conversion Funnel. Finds visitors who reached from_step but never
reached to_step, using an anti-join (NOT IN) rather than reconstructing
each visitor's full cross-table journey -- last_known_action/last_seen
are taken from the from_step event itself (the last thing we know for
certain in the context of this specific funnel gap), avoiding an N+1
per-visitor lookup for what's meant to be a paginated, potentially
large list.

Step -> (table, extra WHERE clause) mapping mirrors
conversion_repository.py's steps -- kept as a separate local mapping
here rather than importing it, consistent with how other domains
(journey_repository, interactions_repository) keep their own
self-contained table/column mappings.
"""

from dataclasses import dataclass
from datetime import date

from app.database.connection import get_connection

_FORM_ID = "cx_diagnostic"

# step_name -> (schema-qualified table, WHERE clause filtering to that step)
_STEP_SOURCES: dict[str, tuple[str, str]] = {
    "contact_us_page_view": ("rudder_schema.pages", "path = '/contact-us'"),
    "form_start": ("rudder_schema.form_start", f"form_id = '{_FORM_ID}'"),
    "form_field_complete": ("rudder_schema.form_field_complete", f"form_id = '{_FORM_ID}'"),
    "form_submit": ("rudder_schema.form_submit", f"form_id = '{_FORM_ID}'"),
    "form_submit_success": ("rudder_schema.form_submit_success", f"form_id = '{_FORM_ID}'"),
}

VALID_FUNNEL_STEPS: frozenset[str] = frozenset(_STEP_SOURCES.keys())


@dataclass(frozen=True)
class DropoffVisitorRow:
    anonymous_id: str
    last_seen: str


def _date_filter_clause(
    start_date: date | None, end_date: date | None, param_prefix: str
) -> tuple[str, dict]:
    """
    Named-parameter date filter, matching conversion_repository.py's
    style. param_prefix distinguishes the "from" and "to" instances
    of these params from each other, since both appear in the same
    query with potentially different needs -- kept identical here,
    but distinct names avoid any collision risk if this ever changes.
    """
    conditions = []
    params: dict = {}
    if start_date is not None:
        key = f"{param_prefix}_start_date"
        conditions.append(f"timestamp >= %({key})s")
        params[key] = start_date
    if end_date is not None:
        key = f"{param_prefix}_end_date"
        conditions.append(f"timestamp < %({key})s + interval '1 day'")
        params[key] = end_date

    if not conditions:
        return "", {}
    return "AND " + " AND ".join(conditions), params


async def get_dropoff_count(
    from_step: str,
    to_step: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> int:
    """
    Total count of visitors who reached from_step but never to_step.
    Caller must validate both steps are in VALID_FUNNEL_STEPS first --
    this function trusts that validation already happened, since table
    names are interpolated from the trusted _STEP_SOURCES map only.

    The date filter only applies to the from_step side -- we're
    asking "who reached from_step within this window and never
    reached to_step at all" (any time), not requiring to_step to also
    fall in the window. Filtering to_step by date as well would wrongly
    count someone as "dropped off" if they converted just outside the
    chosen range.
    """
    from_table, from_filter = _STEP_SOURCES[from_step]
    to_table, to_filter = _STEP_SOURCES[to_step]
    date_clause, date_params = _date_filter_clause(start_date, end_date, "from")

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT COUNT(DISTINCT f.anonymous_id)
                FROM {from_table} f
                WHERE {from_filter} {date_clause}
                  AND f.anonymous_id NOT IN (
                      SELECT anonymous_id FROM {to_table} WHERE {to_filter}
                  )
                """,
                date_params,
            )
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_dropoff_visitors(
    from_step: str,
    to_step: str,
    limit: int,
    offset: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[DropoffVisitorRow]:
    """
    Paginated list of dropped-off visitors, most-recently-seen-at-
    from_step first. last_seen is their from_step timestamp -- see
    module docstring for why we don't reconstruct a full journey here.
    Same from_step-only date scoping as get_dropoff_count above.
    """
    from_table, from_filter = _STEP_SOURCES[from_step]
    to_table, to_filter = _STEP_SOURCES[to_step]
    date_clause, date_params = _date_filter_clause(start_date, end_date, "from")

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT DISTINCT ON (f.anonymous_id)
                    f.anonymous_id, f.timestamp
                FROM {from_table} f
                WHERE {from_filter} {date_clause}
                  AND f.anonymous_id NOT IN (
                      SELECT anonymous_id FROM {to_table} WHERE {to_filter}
                  )
                ORDER BY f.anonymous_id, f.timestamp DESC
                """,
                date_params,
            )
            all_rows = await cur.fetchall()

    sorted_rows = sorted(all_rows, key=lambda r: r[1], reverse=True)
    page_rows = sorted_rows[offset : offset + limit]

    return [DropoffVisitorRow(anonymous_id=r[0], last_seen=str(r[1])) for r in page_rows]