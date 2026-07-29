"""
Drop-off Explorer business logic.

Not cached -- parameterized by from_step/to_step/page, same low
hit-rate reasoning as the old mock dropoff explorer and Domain 2's
events list.

Validates from_step/to_step are both real funnel steps AND that
from_step precedes to_step in funnel order -- asking "who reached
form_submit_success but never reached contact_us_page_view" is
nonsensical (success can't happen without the page view already
having occurred), so that combination is rejected here rather than
silently returning a meaningless empty/wrong result.
"""

import logging

from app.core.constants import FUNNEL_STEPS
from app.repositories.dropoff_explorer_repository import (
    VALID_FUNNEL_STEPS,
    get_dropoff_count,
    get_dropoff_visitors,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.dropoff_explorer import DropoffSummary, DropoffVisitor

logger = logging.getLogger(__name__)


class InvalidFunnelStepError(Exception):
    """Raised when from_step/to_step aren't valid, or from_step doesn't precede to_step."""


def _validate_steps(from_step: str, to_step: str) -> None:
    if from_step not in VALID_FUNNEL_STEPS:
        raise InvalidFunnelStepError(f"Invalid from_step: {from_step}")
    if to_step not in VALID_FUNNEL_STEPS:
        raise InvalidFunnelStepError(f"Invalid to_step: {to_step}")
    if from_step == to_step:
        raise InvalidFunnelStepError("from_step and to_step must differ")
    if FUNNEL_STEPS.index(from_step) >= FUNNEL_STEPS.index(to_step):
        raise InvalidFunnelStepError(
            f"from_step ({from_step}) must come before to_step ({to_step}) in funnel order"
        )


async def get_dropoff_summary(from_step: str, to_step: str) -> DropoffSummary:
    _validate_steps(from_step, to_step)
    count = await get_dropoff_count(from_step, to_step)
    return DropoffSummary(from_step=from_step, to_step=to_step, total_dropoff=count)


async def get_dropoff_visitors_page(
    from_step: str, to_step: str, page: int, page_size: int
) -> PaginatedResponse[DropoffVisitor]:
    _validate_steps(from_step, to_step)
    offset = (page - 1) * page_size

    rows = await get_dropoff_visitors(from_step, to_step, limit=page_size, offset=offset)
    total = await get_dropoff_count(from_step, to_step)

    items = [
        DropoffVisitor(
            anonymous_id=r.anonymous_id, last_known_action=from_step, last_seen=r.last_seen
        )
        for r in rows
    ]
    meta = PaginationMeta.build(page=page, page_size=page_size, total_items=total)
    return PaginatedResponse[DropoffVisitor](items=items, meta=meta)