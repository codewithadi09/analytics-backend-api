"""
Retention repository -- currently backed by mock data.

Per the layered-build plan, this is the ONLY file that changes in
Phase 12 when real PostgreSQL credentials are available.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChurnedUserRow:
    email: str
    user_name: str
    last_seen: str
    total_orders: int
    lifetime_revenue: float
    inactive_for: str


@dataclass(frozen=True)
class ReengagedUserRow:
    email: str
    user_name: str
    went_dark_at: str
    came_back_at: str
    gap_hours: float


@dataclass(frozen=True)
class UserRevenueRow:
    email: str
    user_name: str
    total_orders: int
    lifetime_revenue: float
    avg_order_value: float
    first_order: str
    last_order: str


@dataclass(frozen=True)
class RetentionCurvePointRow:
    days_since_first_visit: int
    retention_pct: float
    retained_users: int


_MOCK_CHURNED_USERS = [
    ChurnedUserRow("alice@example.com", "Alice Nguyen", "2026-07-23T09:14:00", 3, 245.50, "4 days, 2:10:00"),
    ChurnedUserRow("bob@example.com", "Bob Martins", "2026-07-22T18:40:00", 0, 0.0, "4 days, 16:44:00"),
    ChurnedUserRow("carla@example.com", "Carla Diaz", "2026-07-24T11:02:00", 5, 610.00, "3 days, 6:56:00"),
    ChurnedUserRow("dev@example.com", "Dev Patel", "2026-07-21T07:30:00", 1, 42.99, "5 days, 20:28:00"),
]

_MOCK_REENGAGED_USERS = [
    ReengagedUserRow("erin@example.com", "Erin Cole", "2026-07-24T02:00:00", "2026-07-24T19:15:00", 17.25),
    ReengagedUserRow("frank@example.com", "Frank Ito", "2026-07-25T22:10:00", "2026-07-26T14:45:00", 16.58),
    ReengagedUserRow("grace@example.com", "Grace Kim", "2026-07-26T01:30:00", "2026-07-26T13:00:00", 11.5),
]

_MOCK_USER_REVENUE = [
    UserRevenueRow("hana@example.com", "Hana Suzuki", 12, 2140.00, 178.33, "2026-03-02", "2026-07-20"),
    UserRevenueRow("ivan@example.com", "Ivan Petrov", 9, 1875.50, 208.39, "2026-02-14", "2026-07-18"),
    UserRevenueRow("jane@example.com", "Jane Wu", 7, 1420.00, 202.86, "2026-04-01", "2026-07-15"),
    UserRevenueRow("kevin@example.com", "Kevin Brooks", 5, 980.00, 196.00, "2026-05-10", "2026-07-10"),
    UserRevenueRow("lena@example.com", "Lena Fischer", 4, 640.00, 160.00, "2026-05-22", "2026-07-05"),
]

_MOCK_RETENTION_CURVE = [
    RetentionCurvePointRow(days_since_first_visit=0, retention_pct=100.0, retained_users=1240),
    RetentionCurvePointRow(days_since_first_visit=1, retention_pct=18.5, retained_users=230),
    RetentionCurvePointRow(days_since_first_visit=3, retention_pct=11.2, retained_users=139),
    RetentionCurvePointRow(days_since_first_visit=7, retention_pct=7.4, retained_users=92),
    RetentionCurvePointRow(days_since_first_visit=14, retention_pct=4.8, retained_users=60),
    RetentionCurvePointRow(days_since_first_visit=30, retention_pct=2.9, retained_users=36),
]


async def get_churned_users() -> list[ChurnedUserRow]:
    """
    Phase 12 replacement: users with last_event_at older than 3 days,
    left-joined against orders for lifetime_revenue/total_orders.
    """
    return _MOCK_CHURNED_USERS


async def get_reengaged_users() -> list[ReengagedUserRow]:
    """
    Phase 12 replacement: window-function query detecting gaps of
    12+ hours between consecutive events for the same user, followed
    by a subsequent event (i.e. they came back).
    """
    return _MOCK_REENGAGED_USERS


async def get_revenue_per_user() -> list[UserRevenueRow]:
    """
    Phase 12 replacement: per-user aggregate over orders table,
    ordered by lifetime_revenue descending.
    """
    return sorted(_MOCK_USER_REVENUE, key=lambda r: r.lifetime_revenue, reverse=True)


async def get_retention_curve() -> list[RetentionCurvePointRow]:
    """
    Phase 12 replacement: cohort retention query -- percentage of
    users from each first-visit cohort still active N days later.
    """
    return _MOCK_RETENTION_CURVE