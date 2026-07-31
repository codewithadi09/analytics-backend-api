"""
User Journey (cross-session) repository -- unions pages, all 16 click
tables, and all 6 form-funnel tables into one chronological timeline
per anonymous_id, deliberately not reset at session boundaries.

context_session_id is selected alongside each event (not exposed via
the API schema) purely so the service layer can compute session_count
without a second query -- see app/services/journey_service.py.
"""

from dataclasses import dataclass

from app.database.connection import get_connection

# table_name -> (event_category, label SQL expression)
_CLICK_LABELS: dict[str, str] = {
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

_FORM_LABELS: dict[str, str] = {
    "form_start": "first_field",
    "form_field_focus": "field_name",
    "form_field_complete": "field_name",
    "form_field_error": "(field_name || ' (' || error_type || ')')",
    "form_submit": "fields_completed",
    "form_submit_success": "form_id",
}


@dataclass(frozen=True)
class JourneyEventRow:
    event_category: str
    event_type: str
    label: str | None
    page_path: str | None
    timestamp: str
    session_id: int | None


@dataclass(frozen=True)
class ResolvedIdentityRow:
    email: str | None
    name: str | None


def _build_events_query(sort_order: str) -> str:
    """
    sort_order must already be validated as exactly "ASC" or "DESC"
    by the caller before reaching here -- this function trusts that
    validation, same pattern as interaction_type trust in
    interactions_repository.py. It's interpolated directly since SQL
    doesn't allow ORDER BY direction to be a bound parameter.
    """
    parts = [
        "SELECT 'page_view' AS event_category, 'page_view' AS event_type, "
        "NULL::text AS label, path AS page_path, timestamp, context_session_id "
        "FROM rudder_schema.pages WHERE anonymous_id = %(anon_id)s"
    ]
    for table, label_expr in _CLICK_LABELS.items():
        parts.append(
            f"SELECT 'click', '{table}', {label_expr}, context_page_path, "
            f"timestamp, context_session_id "
            f"FROM rudder_schema.{table} WHERE anonymous_id = %(anon_id)s"
        )
    for table, label_expr in _FORM_LABELS.items():
        parts.append(
            f"SELECT 'form_activity', '{table}', {label_expr}, context_page_path, "
            f"timestamp, context_session_id "
            f"FROM rudder_schema.{table} WHERE anonymous_id = %(anon_id)s"
        )
    return " UNION ALL ".join(parts) + f" ORDER BY timestamp {sort_order}"


_EVENTS_QUERY_ASC = _build_events_query("ASC")
_EVENTS_QUERY_DESC = _build_events_query("DESC")


async def get_user_journey_events(
    anonymous_id: str, sort_order: str = "asc"
) -> list[JourneyEventRow]:
    """
    Full chronological timeline for one visitor, across pages + all 16
    click tables + all 6 form-funnel tables. Not paginated -- bounded,
    human-scale per-visitor volume.

    sort_order: "asc" (oldest first, default -- matches original
    behavior) or "desc" (newest first). Any other value falls back to
    "asc" rather than raising, since this is an internal function --
    the API layer is responsible for rejecting invalid values before
    they ever reach here.
    """
    query = _EVENTS_QUERY_DESC if sort_order.lower() == "desc" else _EVENTS_QUERY_ASC
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, {"anon_id": anonymous_id})
            rows = await cur.fetchall()
            return [
                JourneyEventRow(
                    event_category=r[0],
                    event_type=r[1],
                    label=r[2],
                    page_path=r[3],
                    timestamp=str(r[4]),
                    session_id=r[5],
                )
                for r in rows
            ]


async def get_resolved_identity(anonymous_id: str) -> ResolvedIdentityRow | None:
    """
    Most recent identify() call for this visitor, if they've ever
    converted. Returns None if this anonymous_id never submitted the
    form (the common case -- most visitors stay anonymous).
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT context_traits_email, context_traits_name
                FROM rudder_schema.identifies
                WHERE anonymous_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (anonymous_id,),
            )
            row = await cur.fetchone()
            if row is None:
                return None
            return ResolvedIdentityRow(email=row[0], name=row[1])