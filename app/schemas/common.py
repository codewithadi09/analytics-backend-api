"""
Shared response schemas used across every API domain.

Keeping a single envelope shape means the frontend can write one
generic response parser instead of a bespoke one per endpoint.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    """Standard error shape returned in the `detail` field of any 4xx/5xx response."""

    message: str
    code: str = Field(
        description="Machine-readable error code, e.g. 'INVALID_CREDENTIALS', 'TOKEN_EXPIRED'."
    )


class PaginationParams(BaseModel):
    """Query params accepted by any paginated list endpoint."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    page_size: int = Field(default=25, ge=1, le=100, description="Items per page, max 100")


class PaginationMeta(BaseModel):
    """Pagination metadata returned alongside paginated results."""

    page: int
    page_size: int
    total_items: int
    total_pages: int

    @classmethod
    def build(cls, page: int, page_size: int, total_items: int) -> "PaginationMeta":
        total_pages = (total_items + page_size - 1) // page_size if page_size else 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Generic wrapper for any endpoint that returns a list of items."""

    items: list[DataT]
    meta: PaginationMeta