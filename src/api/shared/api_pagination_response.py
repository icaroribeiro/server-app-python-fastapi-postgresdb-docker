from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIPaginationResponse(BaseModel, Generic[T]):
    page: int
    limit: int
    total_pages: int
    total_records: int
    records: list[T]
    previous: str | None = None
    next: str | None = None
