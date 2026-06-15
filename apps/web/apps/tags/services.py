from __future__ import annotations

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService, ExportService, FilterableQueryService
from apps.tags import selectors
from apps.tags.models import Tag


class TagService(AuditableService, FilterableQueryService):
    _MODULE = "tags"
    _RESOURCE_TYPE = "tag"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "created_at"]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_all_tags()

    def _snapshot(self, tag: Tag) -> dict:
        return {"code": tag.code, "name": tag.name}

    def get(self, code: str, *args, **kwargs) -> Tag:
        obj = selectors.get_tag_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Tag", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(self, *, name: str) -> Tag:
        if selectors.tag_exists(name):
            raise AlreadyExistsException(detail=f"Tag '{name}' already exists.")
        obj = Tag.objects.create(name=name, created_by=self.user, updated_by=self.user)
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, *, name: str | None = None) -> Tag:
        obj = self.get(code)
        before = self._snapshot(obj)
        if name is not None:
            if selectors.tag_exists(name, exclude_pk=obj.pk):
                raise AlreadyExistsException(detail=f"Tag '{name}' already exists.")
            obj.name = name
        obj.updated_by = self.user
        obj.save(update_fields=["name", "updated_by", "updated_at"])
        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str) -> None:
        obj = self.get(code)
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=code,
            before=before,
            actor=self.user,
        )


class TagExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Tag",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = ["code", "name", "created_at", "created_by"]
    EXPORT_FILENAME = "tags_export"
    EXPORT_MODULE_NAME = "Tags"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = selectors.get_all_tags()
        if filters:
            search = (filters.get("search") or "").strip()
            if search:
                qs = qs.filter(name__icontains=search)

        rows = self._prepare_rows(list(qs), resolved)

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            "Allowed: csv, xlsx, pdf, json."
        )
