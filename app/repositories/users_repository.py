"""
Users repository -- currently backed by mock data.

Per the layered-build plan, this is the ONLY file that changes in
Phase 12 when real PostgreSQL credentials are available.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DropoffUserRow:
    user_id: str | None
    email: str | None
    user_name: str | None
    last_seen: str


@dataclass(frozen=True)
class RecentOrderRow:
    order_id: str
    email: str
    user_name: str
    order_total: float
    order_date: str
    status: str


# A fixed pool of dropoff users -- in the real query this would
# depend on from_step/to_step, but for mock purposes we return a
# representative mixed set (identified + anonymous) regardless of
# which two steps are picked, so every step-pair combination is
# testable without hand-writing dozens of scenarios.
_MOCK_DROPOFF_USERS = [
    DropoffUserRow("mia@example.com", "mia@example.com", "Mia Chen", "2026-07-25T14:20:00"),
    DropoffUserRow("noah@example.com", "noah@example.com", "Noah Silva", "2026-07-25T09:05:00"),
    DropoffUserRow(None, None, None, "2026-07-26T02:10:00"),
    DropoffUserRow(None, None, None, "2026-07-26T11:45:00"),
    DropoffUserRow("olga@example.com", "olga@example.com", "Olga Petrenko", "2026-07-24T16:30:00"),
]

_MOCK_RECENT_ORDERS = [
    RecentOrderRow("ORD-2001", "hana@example.com", "Hana Suzuki", 178.33, "2026-07-26T10:00:00", "completed"),
    RecentOrderRow("ORD-2002", "ivan@example.com", "Ivan Petrov", 208.39, "2026-07-25T15:30:00", "completed"),
    RecentOrderRow("ORD-2003", "alice@example.com", "Alice Nguyen", 29.00, "2026-07-20T10:11:00", "completed"),
    RecentOrderRow("ORD-2004", "jane@example.com", "Jane Wu", 145.00, "2026-07-24T09:12:00", "refunded"),
    RecentOrderRow("ORD-2005", "kevin@example.com", "Kevin Brooks", 62.50, "2026-07-23T18:40:00", "completed"),
]


async def get_dropoff_users(from_step: str, to_step: str) -> list[DropoffUserRow]:
    """
    Phase 12 replacement: for each user who has a `from_step` event,
    check whether they also have a `to_step` event; return those
    who don't, left-joined against identified_users for email/name.
    """
    return _MOCK_DROPOFF_USERS


async def get_recent_orders() -> list[RecentOrderRow]:
    """
    Phase 12 replacement: SELECT ... FROM orders ORDER BY order_date DESC LIMIT ...
    """
    return sorted(_MOCK_RECENT_ORDERS, key=lambda r: r.order_date, reverse=True)