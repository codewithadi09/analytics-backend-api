"""
Request/response schemas for the users domain: dropoff explorer
and recent orders.
"""

from pydantic import BaseModel, EmailStr, Field


class DropoffUser(BaseModel):
    """A user who completed `from_step` but never reached `to_step`."""

    user_id: str | None = None  # None if not yet identified
    email: EmailStr | None = None
    user_name: str | None = None
    last_seen: str  # ISO 8601 string


class DropoffSummary(BaseModel):
    from_step: str
    to_step: str
    total_dropoff: int = Field(ge=0)
    identified_count: int = Field(ge=0)
    anonymous_count: int = Field(ge=0)


class RecentOrder(BaseModel):
    """One completed order."""

    order_id: str
    email: EmailStr
    user_name: str
    order_total: float = Field(ge=0)
    order_date: str  # ISO 8601 string
    status: str