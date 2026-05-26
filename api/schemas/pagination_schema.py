"""Generic pagination schemas for API responses."""
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of items to return")


class PaginatedMeta(BaseModel):
    """Pagination metadata included in responses."""
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items per page")
    total: int = Field(..., description="Total number of items available")