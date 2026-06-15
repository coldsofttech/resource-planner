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
from apps.projects import selectors
from apps.projects.models import ProjectStatus, ProjectSubStatus


class ProjectStatusService(AuditableService, FilterableQueryService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project_status"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "is_active", "created_at"]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_project_statuses()

    def get(self, code: str, *args, **kwargs) -> ProjectStatus:
        obj = selectors.get_project_status_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectStatus", lookup_field="code", lookup_value=code
            )
        return obj

    def options(self) -> list[dict]:
        return [
            {"code": ps.code, "name": ps.name}
            for ps in selectors.get_project_status_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_project_status_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class ProjectStatusExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "id": "ID",
        "name": "Project Status Name",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "id",
        "name",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "project_statuses_export"
    EXPORT_MODULE_NAME = "Project Statuses"

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

        qs = selectors.get_all_project_statuses()
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


class ProjectSubStatusService(AuditableService, FilterableQueryService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project_sub_status"

    _status_scope: str | None = None

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "order", "is_active", "created_at"]
    default_ordering: list[str] = ["order", "name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        if self._status_scope:
            return selectors.get_project_sub_statuses_by_status(self._status_scope)
        return selectors.get_all_project_sub_statuses()

    def _snapshot(self, obj: ProjectSubStatus) -> dict:
        return {
            "code": obj.code,
            "name": obj.name,
            "main_status_code": obj.main_status.code,
            "order": obj.order,
            "is_active": obj.is_active,
        }

    def get(self, code: str, *args, **kwargs) -> ProjectSubStatus:
        obj = selectors.get_project_sub_status_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectSubStatus", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        status: ProjectStatus,
        is_active: bool = True,
    ) -> ProjectSubStatus:
        if selectors.project_sub_status_exists(name, status):
            raise AlreadyExistsException(
                detail=f"A sub-status named '{name}' already exists for this status."
            )
        next_order = selectors.get_project_sub_status_max_order(status) + 1
        obj = ProjectSubStatus.objects.create(
            name=name,
            main_status=status,
            order=next_order,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> ProjectSubStatus:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_name = kwargs.get("name", obj.name)
        if new_name != obj.name and selectors.project_sub_status_exists(
            new_name, obj.main_status, exclude_pk=obj.pk
        ):
            raise AlreadyExistsException(
                detail=(
                    f"A sub-status named '{new_name}' already exists for this status."
                )
            )

        if "name" in kwargs:
            obj.name = kwargs["name"]
            update_fields.append("name")

        if "is_active" in kwargs:
            obj.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

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
    def activate(self, code: str) -> ProjectSubStatus:
        obj = self.get(code=code)
        if not obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = True
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def deactivate(self, code: str) -> ProjectSubStatus:
        obj = self.get(code=code)
        if obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = False
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        sub_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=sub_code,
            before=before,
            actor=self.user,
        )

    @transaction.atomic
    def reorder(self, status: ProjectStatus, codes: list[str]) -> None:
        all_subs = {ss.code: ss for ss in status.sub_statuses.all()}

        for code in codes:
            if code not in all_subs:
                raise NotFoundException(
                    resource="ProjectSubStatus", lookup_field="code", lookup_value=code
                )

        # Two-pass bulk_update avoids unique constraint violations on
        # (main_status, order)
        parking: list[ProjectSubStatus] = []
        for i, code in enumerate(codes):
            all_subs[code].order = 1_000_000 + i
            parking.append(all_subs[code])
        ProjectSubStatus.objects.bulk_update(parking, ["order"])

        final: list[ProjectSubStatus] = []
        for i, code in enumerate(codes, start=1):
            all_subs[code].order = i
            final.append(all_subs[code])
        ProjectSubStatus.objects.bulk_update(final, ["order"])

    def options(self, status_code: str | None = None) -> list[dict]:
        return [
            {"code": ss.code, "name": ss.name}
            for ss in selectors.get_project_sub_status_options(status_code)
        ]

    def stats(
        self, fields=None, status_code: str | None = None, *args, **kwargs
    ) -> dict:
        all_stats = selectors.get_project_sub_status_stats(status_code)
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class ProjectSubStatusImportService(ImportService):
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
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Sub-status name is required.",
                }
            )
        elif len(name) > 100:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Sub-status name must be 100 characters or fewer.",
                }
            )
        return errors

    def bulk_import(
        self, file, dry_run: bool = False, status: ProjectStatus | None = None
    ) -> dict:
        if status is None:
            raise ValidationException("A parent project status is required for import.")

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
        svc = ProjectSubStatusService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")

            if selectors.project_sub_status_exists(name, status):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": (
                            f"A sub-status named '{name}' already exists "
                            f"for this status."
                        ),
                    }
                )
                continue

            if not dry_run:
                svc.create(name=name, status=status, is_active=is_active)

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class ProjectSubStatusExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Sub-Status Name",
        "main_status": "Main Status",
        "order": "Order",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "name",
        "main_status",
        "order",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "project_sub_statuses_export"
    EXPORT_MODULE_NAME = "Project Sub-Statuses"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
        status: ProjectStatus | None = None,
    ) -> HttpResponse:
        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = selectors.get_all_project_sub_statuses()
        if status:
            qs = qs.filter(main_status=status)
        if filters:
            is_active_raw = filters.get("is_active")
            if is_active_raw not in (None, "", "all"):
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


class ProjectSubStatusGlobalImportService(ImportService):
    """
    Import sub-statuses across all parent statuses; main_status_code is a CSV column.
    """

    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 5_000
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
        if not (row.get("main_status_code") or "").strip():
            errors.append(
                {
                    "row": row_num,
                    "field": "main_status_code",
                    "message": "Main status code is required.",
                }
            )
        name = (row.get("name") or "").strip()
        if not name:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Sub-status name is required.",
                }
            )
        elif len(name) > 100:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Sub-status name must be 100 characters or fewer.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False, **kwargs) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"main_status_code", "name"}
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
        svc = ProjectSubStatusService(user=self.user)
        status_cache: dict[str, ProjectStatus | None] = {}

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            main_status_code = row["main_status_code"].strip()
            name = row["name"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")

            if main_status_code not in status_cache:
                status_cache[main_status_code] = selectors.get_project_status_by_code(
                    main_status_code
                )
            parent_status = status_cache[main_status_code]

            if parent_status is None:
                errors.append(
                    {
                        "row": row_num,
                        "field": "main_status_code",
                        "message": f"Project status '{main_status_code}' not found.",
                    }
                )
                continue

            if selectors.project_sub_status_exists(name, parent_status):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": (
                            f"A sub-status named '{name}' already exists for "
                            f"this status."
                        ),
                    }
                )
                continue

            if not dry_run:
                svc.create(name=name, status=parent_status, is_active=is_active)

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }
