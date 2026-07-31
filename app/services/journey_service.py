"""
User Journey (cross-session) business logic.

Not cached -- keyed by arbitrary anonymous_id values looked up ad hoc,
same reasoning as the old mock user_journey_service.py: caching would
need unbounded key growth for a low hit rate, and this domain benefits
from reflecting current state rather than a stale snapshot.

All summary stats (total_events, session_count, first_seen, last_seen,
has_converted) are computed here from the one event list the
repository already fetched -- no reason to re-query the database for
data derivable from rows already in hand.

first_seen/last_seen are always the true chronological earliest/latest
event, independent of sort_order -- sort_order only affects the order
of the events list itself, not what counts as "first" or "last".
"""

import logging

from app.repositories.journey_repository import (
    get_resolved_identity,
    get_user_journey_events,
)
from app.schemas.journey import JourneyEvent, ResolvedIdentity, UserJourneyResponse
from app.repositories.journey_repository import (
    get_visitor_count as repo_get_visitor_count,
    get_visitors_page as repo_get_visitors_page,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.journey import VisitorSummary

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when anonymous_id has zero events across every source table."""


async def get_user_journey(
    anonymous_id: str, sort_order: str = "asc"
) -> UserJourneyResponse:
    rows = await get_user_journey_events(anonymous_id, sort_order)

    if not rows:
        raise UserNotFoundError(f"No journey found for anonymous_id={anonymous_id}")

    session_ids = {r.session_id for r in rows if r.session_id is not None}
    has_converted = any(r.event_type == "form_submit_success" for r in rows)

    # rows[0]/rows[-1] are only "first"/"last" chronologically when
    # sort_order is asc -- compute these independent of display order
    # instead of trusting list position, so desc mode still reports
    # the correct first_seen/last_seen rather than swapped values.
    timestamps = [r.timestamp for r in rows]
    first_seen = min(timestamps)
    last_seen = max(timestamps)

    identity_row = await get_resolved_identity(anonymous_id)
    resolved_identity = (
        ResolvedIdentity(email=identity_row.email, name=identity_row.name)
        if identity_row is not None
        else None
    )

    events = [
        JourneyEvent(
            event_category=r.event_category,
            event_type=r.event_type,
            label=r.label,
            page_path=r.page_path,
            timestamp=r.timestamp,
        )
        for r in rows
    ]

    return UserJourneyResponse(
        anonymous_id=anonymous_id,
        resolved_identity=resolved_identity,
        total_events=len(rows),
        session_count=len(session_ids),
        first_seen=first_seen,
        last_seen=last_seen,
        has_converted=has_converted,
        events=events,
    )

async def get_visitors_page(
    search: str | None, page: int, page_size: int
) -> PaginatedResponse[VisitorSummary]:
    """Not cached -- parameterized by search+page, same reasoning as every other filtered list."""
    offset = (page - 1) * page_size

    rows = await repo_get_visitors_page(search, limit=page_size, offset=offset)
    total = await repo_get_visitor_count(search)

    items = [
        VisitorSummary(
            anonymous_id=r.anonymous_id, email=r.email, name=r.name,
            first_seen=r.first_seen, last_seen=r.last_seen,
        )
        for r in rows
    ]
    meta = PaginationMeta.build(page=page, page_size=page_size, total_items=total)
    return PaginatedResponse[VisitorSummary](items=items, meta=meta)