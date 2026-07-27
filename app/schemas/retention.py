"""
Request/response schemas for retention endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class ChurnedUser(BaseModel):
    """A named user with no activity in the past 3 days."""

    email: EmailStr
    user_name: str
    last_seen: str  # ISO 8601 string
    total_orders: int = Field(ge=0)
    lifetime_revenue: float = Field(ge=0)
    inactive_for: str  # human-readable duration, e.g. "3 days, 4:12:00"


class ReengagedUser(BaseModel):
    """A user who went dark 12+ hours and then returned."""

    email: EmailStr
    user_name: str
    went_dark_at: str
    came_back_at: str
    gap_hours: float = Field(ge=0)


class ReengagedUsersResponse(BaseModel):
    users: list[ReengagedUser]
    avg_gap_hours: float = Field(ge=0)


class UserRevenue(BaseModel):
    """Lifetime value for one identified, paying customer."""

    email: EmailStr
    user_name: str
    total_orders: int = Field(ge=0)
    lifetime_revenue: float = Field(ge=0)
    avg_order_value: float = Field(ge=0)
    first_order: str
    last_order: str


class RetentionCurvePoint(BaseModel):
    """Percentage of users still active N days after first visit."""

    days_since_first_visit: int = Field(ge=0)
    retention_pct: float = Field(ge=0, le=100)
    retained_users: int = Field(ge=0)


class RetentionCurveResponse(BaseModel):
    points: list[RetentionCurvePoint]