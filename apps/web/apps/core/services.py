from __future__ import annotations

import math
from abc import ABC, abstractmethod

from django.db.models import Q
from django.http import HttpResponse

from .types import ListParams, PaginatedResult, Pagination, SortParam


class BaseService:
    def __init__(self, **context):
        self.context = context


class ContextService(BaseService):
    def __init__(self, user=None, request=None):
        super().__init__(user=user, request=request)
        self.user = user
        self.request = request


class AuditableService(ContextService):
    """Mixin providing module/resource-type identifiers for audit logging."""

    _MODULE: str = ""
    _RESOURCE_TYPE: str = ""


class QueryService(ContextService, ABC):
    @abstractmethod
    def list(self, params: ListParams | None = None, **kwargs):
        pass

    @abstractmethod
    def get(self, *args, **kwargs):
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
    def bulk_import(self, *args, **kwargs):
        pass

    @abstractmethod
    def validate_row(self, *args, **kwargs):
        pass

    @abstractmethod
    def validate_file(self, file, *args, **kwargs):
        pass


class ExportService(ContextService, ABC):
    """Base class for export services.

    Subclasses must set EXPORT_FIELD_LABELS, DEFAULT_EXPORT_FIELDS, EXPORT_FILENAME,
    and EXPORT_MODULE_NAME, then implement export().
    """

    EXPORT_FIELD_LABELS: dict[str, str] = {}
    DEFAULT_EXPORT_FIELDS: list[str] = []
    EXPORT_FILENAME: str = "export"
    EXPORT_MODULE_NAME: str = "Export"

    # ------------------------------------------------------------------ #
    # Abstract interface
    # ------------------------------------------------------------------ #

    @abstractmethod
    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        pass

    # ------------------------------------------------------------------ #
    # App metadata — sourced from Configurations, with safe fallbacks
    # ------------------------------------------------------------------ #

    def _get_app_title(self) -> str:
        from apps.configurations.selectors import General

        try:
            return General.get_app_name()
        except Exception:
            return "Resource Planner"

    def _get_base_url(self) -> str:
        from apps.configurations.selectors import General

        try:
            return General.get_app_url()
        except Exception:
            return ""

    # ------------------------------------------------------------------ #
    # Field value formatting — generic across model types
    # ------------------------------------------------------------------ #

    def _get_field_value(self, obj, field: str) -> str:
        value = getattr(obj, field, None)
        if value is None:
            return ""
        # User FK fields (created_by / updated_by)
        if hasattr(value, "get_full_name") and hasattr(value, "email"):
            return value.get_full_name() or value.email or str(value)
        # Boolean
        if isinstance(value, bool):
            return "Yes" if value else "No"
        # Datetime / date
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d %H:%M")
        return str(value)

    def _prepare_rows(self, objects: list, fields: list[str]) -> list[dict[str, str]]:
        """Convert model instances to display-name-keyed dicts for exportcore."""
        return [
            {self.EXPORT_FIELD_LABELS[f]: self._get_field_value(obj, f) for f in fields}
            for obj in objects
        ]

    # ------------------------------------------------------------------ #
    # Format renderers — delegate to exportcore, wrap in HttpResponse
    # ------------------------------------------------------------------ #

    def _export_csv(self, rows: list[dict[str, str]]) -> HttpResponse:
        from exportcore import export_to_csv

        content = export_to_csv(rows)
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = (
            f"attachment; filename={self.EXPORT_FILENAME}.csv"
        )
        return response

    def _export_xlsx(self, rows: list[dict[str, str]]) -> HttpResponse:
        from exportcore import export_to_xlsx

        content = export_to_xlsx(rows, title=self.EXPORT_MODULE_NAME)
        response = HttpResponse(
            content,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = (
            f"attachment; filename={self.EXPORT_FILENAME}.xlsx"
        )
        return response

    def _export_pdf(self, rows: list[dict[str, str]]) -> HttpResponse:
        from exportcore import export_to_pdf

        content = export_to_pdf(
            rows=rows,
            title=self.EXPORT_MODULE_NAME,
            app_title=self._get_app_title(),
            base_url=self._get_base_url(),
        )
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f"attachment; filename={self.EXPORT_FILENAME}.pdf"
        )
        return response

    def _export_json(self, rows: list[dict[str, str]]) -> HttpResponse:
        from exportcore import export_to_json

        content = export_to_json(rows)
        response = HttpResponse(content, content_type="application/json")
        response["Content-Disposition"] = (
            f"attachment; filename={self.EXPORT_FILENAME}.json"
        )
        return response


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
    # When True, defaults is_active=True if the caller omits the is_active filter.
    filter_active_by_default: bool = False

    @abstractmethod
    def get_queryset(self):
        pass

    def apply_filters(self, qs, filters: dict):
        for param, lookup in self.filterable_fields.items():
            value = filters.get(param)
            if value not in (None, ""):
                qs = qs.filter(**{lookup: value})

        if self.filter_active_by_default:
            is_active_raw = filters.get("is_active")
            if is_active_raw in (None, ""):
                qs = qs.filter(is_active=True)
            elif str(is_active_raw).lower() != "all":
                qs = qs.filter(
                    is_active=str(is_active_raw).lower() not in ("false", "0")
                )

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

    def _snapshot(self, obj) -> dict:
        """Override in subclasses to return an audit-ready dict snapshot of obj."""
        return {}
