from math import ceil
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta


def paginate(items: list[Any], total: int, page: int, limit: int) -> dict[str, Any]:
    return {
        "data": items,
        "meta": {
            "total": total, "page": page, "limit": limit,
            "total_pages": ceil(total / limit) if limit > 0 else 0,
        },
    }
