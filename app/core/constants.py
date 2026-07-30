"""
Shared constants used across the application.

Nothing here reads environment variables or does I/O — pure static
values only. Env-dependent config lives in core/config.py.
"""

from enum import Enum


# ── Real RudderStack event/table names ───────────────────────
# Replaces the original fake e-commerce EventName enum (page_view,
# product_added, order_completed, etc.) from Phases 1-11. These are
# the confirmed real event/table names in rudder_schema, per the
# handoff doc's Section 6 table inventory and every domain built in
# Phase 12. faq_expand/accordion_expand/stat_expand/view_more_btn_click
# are confirmed to EXIST as tables but haven't had their columns
# queried by any domain yet -- listed here as known event names only,
# not implying anything about their internal shape.

class EventName(str, Enum):
    # Click interactions (16 tables, unified in Domain 2)
    CTA_CLICK = "cta_click"
    NAV_CLICK = "nav_click"
    MENU_CLICK = "menu_click"
    FOOTER_CLICK = "footer_click"
    SERVICE_CARD_CLICK = "service_card_click"
    BLOG_CARD_CLICK = "blog_card_click"
    SITEMAP_CARD_CLICK = "sitemap_card_click"
    WORK_CARD_CLICK = "work_card_click"
    BLOG_CLICK = "blog_click"
    CASE_STUDY_CLICK = "case_study_click"
    CASE_STUDY_CTA_CLICK = "case_study_cta_click"
    OPERATING_RING_CLICK = "operating_ring_click"
    SOCIAL_CLICK = "social_click"
    TAG_FILTER_CLICK = "tag_filter_click"
    PAGINATION_CLICK = "pagination_click"
    CAROUSEL_CLICK = "carousel_click"

    # Content-expansion interactions (tables confirmed to exist,
    # columns not yet inspected by any domain)
    FAQ_EXPAND = "faq_expand"
    ACCORDION_EXPAND = "accordion_expand"
    STAT_EXPAND = "stat_expand"
    VIEW_MORE_BTN_CLICK = "view_more_btn_click"

    # Engagement (Domain 5)
    SCROLL_DEPTH = "scroll_depth"
    PAGE_ENGAGED = "page_engaged"

    # Form funnel -- cx_diagnostic (Domains 6-7)
    FORM_START = "form_start"
    FORM_FIELD_FOCUS = "form_field_focus"
    FORM_FIELD_COMPLETE = "form_field_complete"
    FORM_FIELD_ERROR = "form_field_error"
    FORM_SUBMIT = "form_submit"
    FORM_SUBMIT_SUCCESS = "form_submit_success"
    


# ── Real conversion funnel steps ─────────────────────────────
# Matches exactly the step_name values produced by
# app/repositories/conversion_repository.py. Deliberately NOT built
# from EventName above -- "contact_us_page_view" is a page view
# FILTERED by path, not a distinct RudderStack event name, so the two
# concepts (raw event names vs. named funnel stages) are no longer
# the same thing and shouldn't be coupled together the way the old
# fake e-commerce funnel coupled them.
FUNNEL_STEPS: list[str] = [
    "contact_us_page_view",
    "form_start",
    "form_field_complete",
    "form_submit",
    "form_submit_success",
]


# ── Auth ──────────────────────────────────────────────────────

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# ── Redis key namespacing ────────────────────────────────────

class RedisKeyPrefix(str, Enum):
    CACHE = "cache"
    RATE_LIMIT = "ratelimit"
    JWT_BLACKLIST = "jwt:blacklist"
    EMAIL_VERIFICATION = "email:verify"
    PASSWORD_RESET = "password:reset"
    REFRESH_TOKEN = "refresh:token"       # ADD -- opaque token -> user_id
    REFRESH_TOKEN_BY_USER = "refresh:user"  # ADD -- user_id -> their current active token


def build_redis_key(prefix: RedisKeyPrefix, *parts: str) -> str:
    """
    Builds a namespaced Redis key, e.g.:
        build_redis_key(RedisKeyPrefix.CACHE, "dashboard", "kpis")
        -> "cache:dashboard:kpis"
    """
    return ":".join([prefix.value, *parts])


# ── Cache TTL tiers (seconds) ─────────────────────────────────

class CacheTTL:
    SHORT = 30
    MEDIUM = 60
    LONG = 300
    
EMAIL_VERIFICATION_TTL_SECONDS = 60 * 60 * 24  # 24 hours
PASSWORD_RESET_TTL_SECONDS = 60 * 30  # 30 minutes -- shorter than email verification, higher-risk token
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days

# ── Pagination defaults ───────────────────────────────────────

class PaginationDefaults:
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100