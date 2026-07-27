"""
User journey repository -- currently backed by mock data.

Per the layered-build plan, this is the ONLY file that changes in
Phase 12 when real PostgreSQL credentials are available.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IdentifiedUserRow:
    user_id: str
    user_name: str


@dataclass(frozen=True)
class UserCountsRow:
    total_identified_users: int
    total_users: int
    anonymous_users: int


@dataclass(frozen=True)
class JourneyEventRow:
    event_name: str
    event_timestamp: str
    page_path: str | None = None
    product_name: str | None = None
    price: float | None = None
    order_id: str | None = None
    order_total: float | None = None
    service_name: str | None = None
    form_name: str | None = None


_MOCK_IDENTIFIED_USERS = [
    IdentifiedUserRow("alice@example.com", "Alice Nguyen"),
    IdentifiedUserRow("bob@example.com", "Bob Martins"),
    IdentifiedUserRow("hana@example.com", "Hana Suzuki"),
]

_MOCK_COUNTS = UserCountsRow(
    total_identified_users=3,
    total_users=1240,
    anonymous_users=1237,
)

_MOCK_JOURNEYS: dict[str, list[JourneyEventRow]] = {
    "alice@example.com": [
        JourneyEventRow("page_view", "2026-07-20T09:58:00", page_path="/"),
        JourneyEventRow("page_view", "2026-07-20T09:59:10", page_path="/pricing"),
        JourneyEventRow("user_signed_up", "2026-07-20T10:01:30"),
        JourneyEventRow("viewed_service", "2026-07-20T10:03:00", service_name="Analytics Pro"),
        JourneyEventRow("product_clicked", "2026-07-20T10:05:40", product_name="Starter Plan", price=29.0),
        JourneyEventRow("product_added", "2026-07-20T10:06:20", product_name="Starter Plan", price=29.0),
        JourneyEventRow("cart_viewed", "2026-07-20T10:07:00"),
        JourneyEventRow("checkout_started", "2026-07-20T10:08:15"),
        JourneyEventRow("order_completed", "2026-07-20T10:11:00", order_id="ORD-1001", order_total=29.0),
    ],
    "bob@example.com": [
        JourneyEventRow("page_view", "2026-07-22T18:20:00", page_path="/"),
        JourneyEventRow("page_view", "2026-07-22T18:22:00", page_path="/blog/getting-started"),
    ],
    "hana@example.com": [
        JourneyEventRow("page_view", "2026-03-01T08:00:00", page_path="/"),
        JourneyEventRow("user_signed_up", "2026-03-01T08:05:00"),
        JourneyEventRow("form_submitted", "2026-03-01T08:10:00", form_name="Contact Sales"),
        JourneyEventRow("order_completed", "2026-03-02T14:00:00", order_id="ORD-0501", order_total=178.33),
    ],
}


async def get_all_identified_users() -> list[IdentifiedUserRow]:
    """Phase 12 replacement: SELECT DISTINCT user_id, user_name FROM identified_users."""
    return _MOCK_IDENTIFIED_USERS


async def get_user_counts() -> UserCountsRow:
    """Phase 12 replacement: dataset-wide COUNT queries against the users table."""
    return _MOCK_COUNTS


async def get_user_journey(user_id: str) -> list[JourneyEventRow]:
    """
    Phase 12 replacement: SELECT * FROM events WHERE user_id = %s
    ORDER BY event_timestamp ASC.
    """
    return _MOCK_JOURNEYS.get(user_id, [])