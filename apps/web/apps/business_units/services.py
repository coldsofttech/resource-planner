from __future__ import annotations

import csv
import io
import os

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.business_units import selectors
from apps.business_units.models import BusinessUnit
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import (
    AuditableService,
    ExportService,
    FilterableQueryService,
    ImportService,
)


class BusinessUnitService(AuditableService, FilterableQueryService):
    _MODULE = "business_units"
    _RESOURCE_TYPE = "business_unit"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["name", "short_name"]
    sortable_fields: list[str] = ["name", "short_name", "is_active", "created_at"]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_business_units()

    def _snapshot(self, bu: BusinessUnit) -> dict:
        return {
            "code": bu.code,
            "name": bu.name,
            "short_name": bu.short_name,
            "is_active": bu.is_active,
        }

    def get(self, code: str, *args, **kwargs) -> BusinessUnit:
        obj = selectors.get_business_unit_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Business Unit", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self, *, name: str, short_name: str, is_active: bool = True
    ) -> BusinessUnit:
        if selectors.business_unit_name_exists(name):
            raise AlreadyExistsException(
                detail=f"A business unit named '{name}' already exists."
            )
        bu = BusinessUnit.objects.create(
            name=name,
            short_name=short_name,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=bu.code,
            after=self._snapshot(bu),
            actor=self.user,
        )
        return bu

    @transaction.atomic
    def update(self, code: str, **kwargs) -> BusinessUnit:
        bu = self.get(code=code)
        before = self._snapshot(bu)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "name" in kwargs:
            new_name = kwargs["name"]
            if new_name != bu.name and selectors.business_unit_name_exists(
                new_name, exclude_pk=bu.pk
            ):
                raise AlreadyExistsException(
                    detail=f"A business unit named '{new_name}' already exists."
                )
            bu.name = new_name
            update_fields.append("name")

        if "short_name" in kwargs:
            bu.short_name = kwargs["short_name"]
            update_fields.append("short_name")

        if "is_active" in kwargs:
            bu.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        bu.updated_by = self.user
        bu.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=bu.code,
            before=before,
            after=self._snapshot(bu),
            actor=self.user,
        )
        return bu

    @transaction.atomic
    def activate(self, code: str) -> BusinessUnit:
        bu = self.get(code=code)
        if not bu.is_active:
            before = self._snapshot(bu)
            bu.is_active = True
            bu.updated_by = self.user
            bu.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=bu.code,
                before=before,
                after=self._snapshot(bu),
                actor=self.user,
            )
        return bu

    @transaction.atomic
    def deactivate(self, code: str) -> BusinessUnit:
        bu = self.get(code=code)
        if bu.is_active:
            before = self._snapshot(bu)
            bu.is_active = False
            bu.updated_by = self.user
            bu.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=bu.code,
                before=before,
                after=self._snapshot(bu),
                actor=self.user,
            )
        return bu

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        bu = self.get(code=code)
        bu_code = bu.code
        before = self._snapshot(bu)
        bu.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=bu_code,
            before=before,
            actor=self.user,
        )

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_business_unit_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats

    def options(self) -> list[dict]:
        return [
            {"code": bu.code, "name": bu.name}
            for bu in selectors.get_active_business_units()
        ]


class BusinessUnitImportService(ImportService):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 1_000
    MAX_IMPORT_FILE_SIZE_MB = 5

    def validate_file(self, file) -> None:
        _, ext = os.path.splitext(file.name)
        if ext.lower().lstrip(".") not in self.SUPPORTED_IMPORT_FORMATS:
            raise ValidationException(
                "Unsupported file format. Allowed: "
                f"{', '.join(self.SUPPORTED_IMPORT_FORMATS)}."
            )
        file_size_mb = file.size / (1024 * 1024)
        if file_size_mb > self.MAX_IMPORT_FILE_SIZE_MB:
            raise ValidationException(
                "File too large. Maximum allowed size: "
                f"{self.MAX_IMPORT_FILE_SIZE_MB} MB."
            )

    def validate_row(self, row: dict, row_num: int) -> list[dict]:
        errors: list[dict] = []
        name = (row.get("name") or "").strip()
        short_name = (row.get("short_name") or "").strip()

        if not name:
            errors.append(
                {"row": row_num, "field": "name", "message": "Name is required."}
            )
        elif len(name) > 255:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Name must be 255 characters or fewer.",
                }
            )

        if not short_name:
            errors.append(
                {
                    "row": row_num,
                    "field": "short_name",
                    "message": "Short name is required.",
                }
            )
        elif len(short_name) > 10:
            errors.append(
                {
                    "row": row_num,
                    "field": "short_name",
                    "message": "Short name must be 10 characters or fewer.",
                }
            )

        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"name", "short_name"}
        actual_columns = set(reader.fieldnames or [])
        missing = required_columns - actual_columns
        if missing:
            raise ValidationException(
                f"Missing required column(s): {', '.join(sorted(missing))}."
            )

        rows = list(reader)
        if len(rows) > self.MAX_IMPORT_ROWS:
            raise ValidationException(
                f"Too many rows. Maximum allowed: {self.MAX_IMPORT_ROWS}."
            )

        total = len(rows)
        created_rows: list[dict] = []
        errors: list[dict] = []
        bu_svc = BusinessUnitService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            short_name = row["short_name"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")

            if selectors.business_unit_name_exists(name):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": f"A business unit named '{name}' already exists.",
                    }
                )
                continue

            if not dry_run:
                bu_svc.create(name=name, short_name=short_name, is_active=is_active)

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class BusinessUnitExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Name",
        "short_name": "Short Name",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "name",
        "short_name",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "business_units_export"
    EXPORT_MODULE_NAME = "Business Units"

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

        qs = selectors.get_all_business_units()
        if filters:
            is_active_raw = filters.get("is_active")
            if is_active_raw in (None, ""):
                qs = qs.filter(is_active=True)
            elif str(is_active_raw).lower() != "all":
                qs = qs.filter(
                    is_active=str(is_active_raw).lower() not in ("false", "0")
                )
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
