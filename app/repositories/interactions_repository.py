"""
Interactions / Click Analytics repository -- unifies 16 real
click-interaction tables into one normalized query surface.

Each table has a different "label" column and its own context_page_path
column (no join against pages needed -- context_page_path is already
present on every one of these tables). Table names are drawn only from
the hardcoded _LABEL_EXPRESSIONS map below, never from raw user input,
so building UNION ALL SQL by string-formatting table names here is safe
-- interaction_type from the API is validated against VALID_INTERACTION_TYPES
before it ever reaches this module.
"""

from dataclasses import dataclass
from datetime import date

from app.database.connection import get_connection

# table_name -> SQL expression that produces this table's "label" text.
# Order here also defines the UNION ALL order for count/leaderboard queries.
_LABEL_EXPRESSIONS: dict[str, str] = {
    "cta_click": "button_text",
    "nav_click": "button_text",
    "menu_click": "button_text",
    "footer_click": "button_text",
    "service_card_click": "card_title",
    "blog_card_click": "card_title",
    "sitemap_card_click": "card_title",
    "work_card_click": "card_title",
    "blog_click": "blog_title",
    "case_study_click": "case_study_title",
    "case_study_cta_click": "cta_text",
    "operating_ring_click": "circle_title",
    "social_click": "social_platform",
    "tag_filter_click": "tag_label",
    "pagination_click": "(content_type || ' - page ' || page_number::text)",
    "carousel_click": "carousel_name",
}

VALID_INTERACTION_TYPES: frozenset[str] = frozenset(_LABEL_EXPRESSIONS.keys())


@dataclass(frozen=True)
class InteractionTypeCountRow:
    interaction_type: str
    count: int


@dataclass(frozen=True)
class InteractionEventRow:
    interaction_type: str
    label: str | None
    page_path: str | None
    timestamp: str


def _date_filter_clause(
    start_date: date | None, end_date: date | None, prefix: str = "WHERE"
) -> tuple[str, list]:
    """
    Same pattern as traffic_repository's helper -- kept local rather
    than shared, consistent with every other repository in this
    project being self-contained.
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


def _count_query(
    start_date: date | None, end_date: date | None
) -> tuple[str, list]:
    """
    Builds the 16-way UNION ALL count query, one COUNT(*) per table.

    The same date clause is repeated inside every one of the 16
    SELECTs -- each table has its own timestamp column, so filtering
    can't happen once at the end, it has to happen per-subquery. The
    parameter list is built to match: the date params appear once per
    table, in the same order as the UNION parts.
    """
    clause, clause_params = _date_filter_clause(start_date, end_date, prefix="WHERE")
    parts = []
    all_params: list = []

    for table in _LABEL_EXPRESSIONS:
        parts.append(
            f"SELECT '{table}' AS interaction_type, COUNT(*) AS count "
            f"FROM rudder_schema.{table} {clause}"
        )
        all_params.extend(clause_params)

    query = " UNION ALL ".join(parts) + " ORDER BY count DESC"
    return query, all_params


def _events_query_all_types(
    start_date: date | None, end_date: date | None
) -> tuple[str, list]:
    """
    Builds the 16-way UNION ALL raw-events query, across every table.
    Returns the query with a trailing LIMIT %s OFFSET %s -- caller
    appends (limit, offset) to the returned params list.
    """
    clause, clause_params = _date_filter_clause(start_date, end_date, prefix="WHERE")
    parts = []
    all_params: list = []

    for table, label_expr in _LABEL_EXPRESSIONS.items():
        parts.append(
            f"SELECT '{table}' AS interaction_type, {label_expr} AS label, "
            f"context_page_path AS page_path, timestamp "
            f"FROM rudder_schema.{table} {clause}"
        )
        all_params.extend(clause_params)

    query = " UNION ALL ".join(parts) + " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
    return query, all_params


def _events_query_single_type(
    table: str, start_date: date | None, end_date: date | None
) -> tuple[str, list]:
    """Single-table events query -- used when the caller filters by type."""
    label_expr = _LABEL_EXPRESSIONS[table]
    clause, clause_params = _date_filter_clause(start_date, end_date, prefix="WHERE")
    query = (
        f"SELECT '{table}' AS interaction_type, {label_expr} AS label, "
        f"context_page_path AS page_path, timestamp "
        f"FROM rudder_schema.{table} {clause} "
        f"ORDER BY timestamp DESC LIMIT %s OFFSET %s"
    )
    return query, clause_params


async def get_interaction_counts(
    start_date: date | None = None, end_date: date | None = None
) -> list[InteractionTypeCountRow]:
    """Per-table interaction counts, ordered highest first -- the leaderboard."""
    query, params = _count_query(start_date, end_date)
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [InteractionTypeCountRow(interaction_type=r[0], count=r[1]) for r in rows]


async def get_interactions_page(
    interaction_type: str | None,
    limit: int,
    offset: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[InteractionEventRow]:
    """
    Paginated raw interaction events, newest first.

    If interaction_type is given, queries only that one table -- avoids
    scanning all 16 tables when the caller only wants one click type.
    Caller (service layer) must validate interaction_type against
    VALID_INTERACTION_TYPES before calling this -- this function trusts
    that validation already happened.
    """
    if interaction_type is not None:
        query, params = _events_query_single_type(interaction_type, start_date, end_date)
    else:
        query, params = _events_query_all_types(start_date, end_date)

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (*params, limit, offset))
            rows = await cur.fetchall()
            return [
                InteractionEventRow(
                    interaction_type=r[0], label=r[1], page_path=r[2], timestamp=str(r[3])
                )
                for r in rows
            ]