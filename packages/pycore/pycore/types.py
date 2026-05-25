from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar

T = TypeVar("T")


@dataclass
class Pagination:
    total_count: int
    total_pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_previous: bool


@dataclass
class PaginatedResult(Generic[T]):
    results: list[T]
    pagination: Pagination


@dataclass
class SortParam:
    sort_by: str = "id"
    direction: Literal["asc", "desc"] = "asc"


@dataclass
class ListParams:
    filters: dict = field(default_factory=dict)
    search: str = ""
    sorts: list[SortParam] = field(default_factory=lambda: [SortParam()])
    page: int = 1
    page_size: int = 25
