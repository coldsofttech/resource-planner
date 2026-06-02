import math
from abc import ABC, abstractmethod

from django.db.models import Q

from .types import ListParams, PaginatedResult, Pagination, SortParam


class BaseService:
    def __init__(self, **context):
        self.context = context


class ContextService(BaseService):
    def __init__(self, user=None, request=None):
        super().__init__(user=user, request=request)
        self.user = user
        self.request = request


class QueryService(ContextService, ABC):
    @abstractmethod
    def list(self, params: ListParams | None = None, **kwargs):
        pass

    @abstractmethod
    def get(self, pk, *args, **kwargs):
        pass


class CommandService(ContextService, ABC):
    @abstractmethod
    def create(self, *args, **kwargs):
        pass

    @abstractmethod
    def update(self, pk, *args, **kwargs):
        pass

    @abstractmethod
    def delete(self, pk, *args, **kwargs):
        pass


class StatisticsService(ContextService, ABC):
    @abstractmethod
    def stats(self, fields=None, *args, **kwargs):
        pass


class ImportService(ContextService, ABC):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 1000
    MAX_IMPORT_FILE_SIZE_MB = 5

    @abstractmethod
    def bulk_import(self, dry_run=False, *args, **kwargs):
        pass

    @abstractmethod
    def validate_row(self, *args, **kwargs):
        pass

    @abstractmethod
    def validate_file(self, file, *args, **kwargs):
        pass


class ExportService(ContextService, ABC):
    @abstractmethod
    def export(self, filters=None, *args, **kwargs):
        pass


class MetadataService(ContextService, ABC):
    @abstractmethod
    def options(self, fields=None, *args, **kwargs):
        pass


class ServiceContainer:
    def __init__(self, user=None, request=None):
        self.user = user
        self.request = request

        self.query = None
        self.command = None
        self.stats = None
        self.import_ = None
        self.export = None
        self.metadata = None


def paginate_queryset(qs, page: int, page_size: int):
    total_count = qs.count()
    total_pages = math.ceil(total_count / page_size) if total_count else 1
    results = list(qs[(page - 1) * page_size : page * page_size])
    return PaginatedResult(
        results=results,
        pagination=Pagination(
            total_count=total_count,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
    )


class FilterableQueryService(QueryService):
    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = []
    sortable_fields: list[str] = ["id"]
    default_ordering: list[str] = ["id"]

    @abstractmethod
    def get_queryset(self):
        pass

    def apply_filters(self, qs, filters: dict):
        for param, lookup in self.filterable_fields.items():
            value = filters.get(param)
            if value not in (None, ""):
                qs = qs.filter(**{lookup: value})
        return qs

    def apply_search(self, qs, query: str):
        if not query or not self.search_fields:
            return qs
        q_obj = Q()
        for field_name in self.search_fields:
            q_obj |= Q(**{f"{field_name}__icontains": query})
        return qs.filter(q_obj)

    def apply_ordering(self, qs, sorts: list[SortParam]):
        order_fields = [
            f"-{s.sort_by}" if s.direction == "desc" else s.sort_by
            for s in sorts
            if s.sort_by in self.sortable_fields
        ]
        return qs.order_by(*(order_fields or self.default_ordering))

    def list(self, params: ListParams | None = None, **kwargs):
        params = params or ListParams()
        qs = self.get_queryset()
        qs = self.apply_filters(qs, params.filters)
        qs = self.apply_search(qs, params.search)
        qs = self.apply_ordering(qs, params.sorts)
        return paginate_queryset(qs, params.page, params.page_size)
