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
"""

import logging

from app.repositories.journey_repository import (
    get_resolved_identity,
    get_user_journey_events,
)
from app.schemas.journey import JourneyEvent, ResolvedIdentity, UserJourneyResponse

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when anonymous_id has zero events across every source table."""


async def get_user_journey(anonymous_id: str) -> UserJourneyResponse:
    rows = await get_user_journey_events(anonymous_id)

    if not rows:
        raise UserNotFoundError(f"No journey found for anonymous_id={anonymous_id}")

    session_ids = {r.session_id for r in rows if r.session_id is not None}
    has_converted = any(r.event_type == "form_submit_success" for r in rows)

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
        first_seen=rows[0].timestamp,
        last_seen=rows[-1].timestamp,
        has_converted=has_converted,
        events=events,
    )