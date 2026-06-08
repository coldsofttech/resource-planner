from __future__ import annotations

import csv
import io
import os

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
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
from apps.employment_types import selectors
from apps.employment_types.models import EmploymentType


class EmploymentTypeService(AuditableService, FilterableQueryService):
    _MODULE = "employment_types"
    _RESOURCE_TYPE = "employment_type"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "is_active", "is_default", "created_at"]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_employment_types()

    def _snapshot(self, employment_type: EmploymentType) -> dict:
        return {
            "code": employment_type.code,
            "name": employment_type.name,
            "is_active": employment_type.is_active,
            "is_default": employment_type.is_default,
        }

    def get(self, code: str, *args, **kwargs) -> EmploymentType:
        obj = selectors.get_employment_type_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Employment Type", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        is_active: bool = True,
        is_default: bool = False,
    ) -> EmploymentType:
        if selectors.employment_type_exists(name):
            raise AlreadyExistsException(
                detail=f"An employment type named '{name}' already exists."
            )
        employment_type = EmploymentType.objects.create(
            name=name,
            is_active=is_active,
            is_default=is_default,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=employment_type.code,
            after=self._snapshot(employment_type),
            actor=self.user,
        )
        return employment_type

    @transaction.atomic
    def update(self, code: str, **kwargs) -> EmploymentType:
        employment_type = self.get(code=code)
        before = self._snapshot(employment_type)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_name = kwargs.get("name", employment_type.name)
        if new_name != employment_type.name and selectors.employment_type_exists(
            new_name, exclude_pk=employment_type.pk
        ):
            raise AlreadyExistsException(
                detail=f"An employment type named '{new_name}' already exists."
            )

        if "name" in kwargs:
            employment_type.name = kwargs["name"]
            update_fields.append("name")

        if "is_active" in kwargs:
            employment_type.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        if "is_default" in kwargs:
            employment_type.is_default = kwargs["is_default"]
            update_fields.append("is_default")

        employment_type.updated_by = self.user
        employment_type.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=employment_type.code,
            before=before,
            after=self._snapshot(employment_type),
            actor=self.user,
        )
        return employment_type

    @transaction.atomic
    def activate(self, code: str) -> EmploymentType:
        employment_type = self.get(code=code)
        if not employment_type.is_active:
            before = self._snapshot(employment_type)
            employment_type.is_active = True
            employment_type.updated_by = self.user
            employment_type.save(
                update_fields=["is_active", "updated_by", "updated_at"]
            )
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=employment_type.code,
                before=before,
                after=self._snapshot(employment_type),
                actor=self.user,
            )
        return employment_type

    @transaction.atomic
    def deactivate(self, code: str) -> EmploymentType:
        employment_type = self.get(code=code)
        if employment_type.is_active:
            before = self._snapshot(employment_type)
            employment_type.is_active = False
            employment_type.updated_by = self.user
            employment_type.save(
                update_fields=["is_active", "updated_by", "updated_at"]
            )
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=employment_type.code,
                before=before,
                after=self._snapshot(employment_type),
                actor=self.user,
            )
        return employment_type

    @transaction.atomic
    def set_default(self, code: str) -> EmploymentType:
        employment_type = self.get(code=code)
        if not employment_type.is_default:
            before = self._snapshot(employment_type)
            EmploymentType.objects.exclude(pk=employment_type.pk).filter(
                is_default=True
            ).update(is_default=False)
            employment_type.is_default = True
            employment_type.updated_by = self.user
            employment_type.save(
                update_fields=["is_default", "updated_by", "updated_at"]
            )
            AuditService.log_set_default(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=employment_type.code,
                before=before,
                after=self._snapshot(employment_type),
                actor=self.user,
            )
        return employment_type

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        employment_type = self.get(code=code)
        employment_type_code = employment_type.code
        before = self._snapshot(employment_type)
        employment_type.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=employment_type_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> list[dict]:
        return [
            {
                "code": et.code,
                "name": et.name,
                "is_default": et.is_default,
            }
            for et in selectors.get_employment_type_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_employment_type_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class EmploymentTypeImportService(ImportService):
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
        if not name:
            errors.append(
                {"row": row_num, "field": "name", "message": "Name is required."}
            )
        elif len(name) > 100:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Name must be 100 characters or fewer.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"name"}
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
        et_svc = EmploymentTypeService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")
            is_default_raw = (row.get("is_default") or "false").strip().lower()
            is_default = is_default_raw in ("true", "1", "yes")

            if selectors.employment_type_exists(name):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": f"An employment type named '{name}' already exists.",
                    }
                )
                continue

            if not dry_run:
                et_svc.create(
                    name=name,
                    is_active=is_active,
                    is_default=is_default,
                )

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class EmploymentTypeExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Name",
        "is_active": "Active",
        "is_default": "Default",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "name",
        "is_active",
        "is_default",
        "created_at",
    ]
    EXPORT_FILENAME = "employment_types_export"
    EXPORT_MODULE_NAME = "Employment Types"

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

        qs = selectors.get_all_employment_types()
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
            f"Allowed: csv, xlsx, pdf, json."
        )
