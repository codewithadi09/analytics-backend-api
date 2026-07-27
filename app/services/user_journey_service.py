"""
User journey business logic.

Deliberately NOT cached in Redis, unlike the dashboard/funnel/
retention services -- this endpoint is keyed by arbitrary user_id
values searched ad hoc, so caching would either need to cover every
possible user (unbounded key growth, low hit rate) or provide no
benefit. The underlying repository call is cheap per-user anyway.
"""

import logging
from datetime import datetime

from app.repositories.user_journey_repository import (
    get_all_identified_users as repo_get_all_identified_users,
    get_user_counts as repo_get_user_counts,
    get_user_journey as repo_get_user_journey,
)
from app.repositories.user_journey_repository import JourneyEventRow
from app.schemas.user_journey import (
    IdentifiedUser,
    JourneyEvent,
    UserCounts,
    UserJourneyResponse,
)

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when a user_id has no journey events -- maps to 404 in the route."""


def _build_detail(event: JourneyEventRow) -> str:
    """
    Picks the most relevant detail string for an event, mirroring
    the priority order in the Streamlit reference implementation's
    _get_detail() helper.
    """
    if event.product_name:
        detail = event.product_name
        if event.price is not None:
            detail += f" - ${event.price}"
        return detail
    if event.page_path:
        return event.page_path
    if event.service_name:
        return event.service_name
    if event.form_name:
        return event.form_name
    if event.order_id:
        total = event.order_total if event.order_total is not None else ""
        return f"Order #{event.order_id} - ${total}"
    return ""


async def get_identified_users() -> list[IdentifiedUser]:
    rows = await repo_get_all_identified_users()
    return [IdentifiedUser(user_id=r.user_id, user_name=r.user_name) for r in rows]


async def get_dataset_counts() -> UserCounts:
    row = await repo_get_user_counts()
    return UserCounts(
        total_identified_users=row.total_identified_users,
        total_users=row.total_users,
        anonymous_users=row.anonymous_users,
    )


async def get_journey(user_id: str) -> UserJourneyResponse:
    """
    Raises UserNotFoundError if the user has no events -- distinct
    from "user exists but hasn't done anything," which isn't
    representable in this mock data and isn't worth modeling
    separately right now.
    """
    events_raw = await repo_get_user_journey(user_id)
    if not events_raw:
        raise UserNotFoundError(f"No journey found for user_id={user_id}")

    users = await repo_get_all_identified_users()
    user_name = next((u.user_name for u in users if u.user_id == user_id), "Unknown")

    first_ts = datetime.fromisoformat(events_raw[0].event_timestamp)
    last_ts = datetime.fromisoformat(events_raw[-1].event_timestamp)
    duration_minutes = int((last_ts - first_ts).total_seconds() // 60)

    unique_pages = len({e.page_path for e in events_raw if e.page_path})
    event_names = {e.event_name for e in events_raw}

    events = [
        JourneyEvent(
            event_name=e.event_name,
            event_timestamp=e.event_timestamp,
            detail=_build_detail(e),
        )
        for e in events_raw
    ]

    return UserJourneyResponse(
        user_id=user_id,
        user_name=user_name,
        total_events=len(events_raw),
        session_duration_minutes=duration_minutes,
        unique_pages=unique_pages,
        has_purchased="order_completed" in event_names,
        has_signed_up="user_signed_up" in event_names,
        events=events,
    )