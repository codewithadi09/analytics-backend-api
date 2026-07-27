"""
Shared constants used across the application.

Nothing here reads environment variables or does I/O — pure static
values only. Env-dependent config lives in core/config.py.
"""

from enum import Enum


# ── Funnel / event names ─────────────────────────────────────
# These match the RudderStack event names already flowing into
# Postgres (see utils/queries.py in the Streamlit reference app).
# Keeping this as an Enum (not raw strings scattered everywhere)
# means a typo becomes an import-time/type error, not a silent
# empty-result bug in a query.

class EventName(str, Enum):
    PAGE_VIEW = "page_view"
    VIEWED_SERVICE = "viewed_service"
    USER_SIGNED_UP = "user_signed_up"
    FORM_SUBMITTED = "form_submitted"
    PRODUCT_CLICKED = "product_clicked"
    PRODUCT_ADDED = "product_added"
    CART_VIEWED = "cart_viewed"
    CHECKOUT_STARTED = "checkout_started"
    ORDER_COMPLETED = "order_completed"


# Canonical funnel order, top to bottom. Used by the dropoff
# explorer and funnel chart endpoints so the step sequence is
# defined once, not re-typed in every service function.
FUNNEL_STEPS: list[str] = [
    EventName.PAGE_VIEW.value,
    EventName.USER_SIGNED_UP.value,
    EventName.FORM_SUBMITTED.value,
    EventName.PRODUCT_CLICKED.value,
    EventName.PRODUCT_ADDED.value,
    EventName.CART_VIEWED.value,
    EventName.CHECKOUT_STARTED.value,
    EventName.ORDER_COMPLETED.value,
]


# ── Auth ──────────────────────────────────────────────────────

class TokenType(str, Enum):
    ACCESS = "access"
    # Reserved for later if refresh tokens are added (not in Phase 3).
    REFRESH = "refresh"


# ── Redis key namespacing ────────────────────────────────────
# Every Redis key in the app is built through these prefixes so
# keys are grep-able and collisions across features are impossible.

class RedisKeyPrefix(str, Enum):
    CACHE = "cache"                 # cached aggregate query results
    RATE_LIMIT = "ratelimit"        # login rate limiting counters
    JWT_BLACKLIST = "jwt:blacklist" # revoked token jtis (Phase 3)


def build_redis_key(prefix: RedisKeyPrefix, *parts: str) -> str:
    """
    Builds a namespaced Redis key, e.g.:
        build_redis_key(RedisKeyPrefix.CACHE, "dashboard", "kpis")
        -> "cache:dashboard:kpis"

    Centralizing this avoids inconsistent key formats (colon vs
    dash vs no separator) across different services.
    """
    return ":".join([prefix.value, *parts])


# ── Cache TTL tiers (seconds) ─────────────────────────────────
# Different endpoints have different volatility. Rather than one
# flat TTL for everything, group them into tiers so it's a single
# obvious knob to turn per-endpoint.

class CacheTTL:
    SHORT = 30        # e.g. dropoff explorer (user picks steps dynamically)
    MEDIUM = 60        # e.g. KPIs, funnel, revenue — default tier
    LONG = 300          # e.g. retention curve, cohort comparison — changes slowly


# ── Pagination defaults ───────────────────────────────────────

class PaginationDefaults:
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100