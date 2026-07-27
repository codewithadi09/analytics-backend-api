"""
Dashboard repository -- currently backed by mock data.

Per the layered-build plan, this is the ONLY file that changes in
Phase 12 when real PostgreSQL credentials are available. Function
signatures and return shapes are the contract the service layer
depends on -- keep them stable when swapping in real SQL.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class KpiRow:
    total_users: int
    total_orders: int
    total_revenue: float
    avg_order_value: float
    total_signups: int
    total_form_submissions: int


@dataclass(frozen=True)
class FunnelStepRow:
    event_name: str
    users: int


async def get_kpis() -> KpiRow:
    """
    Phase 12 replacement: aggregate query across users/orders/events
    tables, e.g.
        SELECT
            COUNT(DISTINCT user_id) AS total_users,
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(order_total) AS total_revenue,
            AVG(order_total) AS avg_order_value,
            ...
        FROM ...
    """
    return KpiRow(
        total_users=1240,
        total_orders=186,
        total_revenue=14520.75,
        avg_order_value=78.06,
        total_signups=402,
        total_form_submissions=95,
    )


async def get_funnel_steps() -> list[FunnelStepRow]:
    """
    Phase 12 replacement: identity-resolved funnel query, e.g.
        SELECT event_name, COUNT(DISTINCT user_id) AS users
        FROM events
        WHERE event_name = ANY(%s)
        GROUP BY event_name
    ordered according to FUNNEL_STEPS (app/core/constants.py).
    """
    return [
        FunnelStepRow(event_name="page_view", users=1240),
        FunnelStepRow(event_name="user_signed_up", users=402),
        FunnelStepRow(event_name="form_submitted", users=95),
        FunnelStepRow(event_name="product_clicked", users=310),
        FunnelStepRow(event_name="product_added", users=210),
        FunnelStepRow(event_name="cart_viewed", users=198),
        FunnelStepRow(event_name="checkout_started", users=201),
        FunnelStepRow(event_name="order_completed", users=186),
    ]