"""
Request/response schemas for the Interactions / Click Analytics domain.

Unifies 15 distinct click-interaction tables (cta_click, nav_click,
menu_click, footer_click, service_card_click, blog_card_click,
sitemap_card_click, work_card_click, blog_click, case_study_click,
case_study_cta_click, operating_ring_click, social_click,
tag_filter_click, pagination_click, carousel_click) into one
normalized shape. Each source table has a different label column and
inconsistent page_id/source_page_id naming -- this schema is the
normalized contract that hides that from API consumers.
"""

from pydantic import BaseModel, Field


class InteractionTypeCount(BaseModel):
    """One interaction type's total count -- one row in the leaderboard."""

    interaction_type: str = Field(
        description="The source table name, e.g. 'cta_click', 'blog_click'."
    )
    count: int = Field(ge=0)


class InteractionLeaderboardResponse(BaseModel):
    """Response body for GET /interactions/leaderboard."""

    total_interactions: int = Field(ge=0)
    by_type: list[InteractionTypeCount]


class InteractionEvent(BaseModel):
    """One normalized click event, regardless of which of the 15 source tables it came from."""

    interaction_type: str
    label: str | None = Field(
        default=None,
        description="Normalized text from that table's label column "
        "(button_text, blog_title, social_platform, etc.).",
    )
    page_path: str | None = None
    timestamp: str  # ISO 8601 string