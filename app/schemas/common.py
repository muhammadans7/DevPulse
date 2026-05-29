from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T") # creating a placeholder with name = T


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated envelope returned by all list endpoints."""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int
