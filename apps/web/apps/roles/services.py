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
from apps.roles import selectors
from apps.roles.models import Role


class RoleService(AuditableService, FilterableQueryService):
    _MODULE = "roles"
    _RESOURCE_TYPE = "role"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["role"]
    sortable_fields: list[str] = [
        "role",
        "is_active",
        "is_default",
        "is_assignable",
        "is_leadership",
        "created_at",
    ]
    default_ordering: list[str] = ["role"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_roles_with_member_count()

    def apply_filters(self, qs, filters: dict):
        qs = super().apply_filters(qs, filters)
        for field in ("is_assignable", "is_leadership"):
            raw = filters.get(field)
            if raw not in (None, "", "all"):
                qs = qs.filter(**{field: str(raw).lower() not in ("false", "0")})
        return qs

    def _snapshot(self, role: Role) -> dict:
        return {
            "code": role.code,
            "role": role.role,
            "is_active": role.is_active,
            "is_default": role.is_default,
            "is_assignable": role.is_assignable,
            "is_leadership": role.is_leadership,
        }

    def get(self, code: str, *args, **kwargs) -> Role:
        obj = selectors.get_role_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Role", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        role: str,
        is_active: bool = True,
        is_default: bool = False,
        is_assignable: bool = False,
        is_leadership: bool = False,
    ) -> Role:
        if selectors.role_exists(role):
            raise AlreadyExistsException(
                detail=f"A role named '{role}' already exists."
            )
        obj = Role.objects.create(
            role=role,
            is_active=is_active,
            is_default=is_default,
            is_assignable=is_assignable,
            is_leadership=is_leadership,
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
    def update(self, code: str, **kwargs) -> Role:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_role = kwargs.get("role", obj.role)
        if new_role != obj.role and selectors.role_exists(new_role, exclude_pk=obj.pk):
            raise AlreadyExistsException(
                detail=f"A role named '{new_role}' already exists."
            )

        if "role" in kwargs:
            obj.role = kwargs["role"]
            update_fields.append("role")

        if "is_active" in kwargs:
            obj.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        if "is_default" in kwargs:
            obj.is_default = kwargs["is_default"]
            update_fields.append("is_default")

        if "is_assignable" in kwargs:
            obj.is_assignable = kwargs["is_assignable"]
            update_fields.append("is_assignable")

        if "is_leadership" in kwargs:
            obj.is_leadership = kwargs["is_leadership"]
            update_fields.append("is_leadership")

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
    def activate(self, code: str) -> Role:
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
    def deactivate(self, code: str) -> Role:
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
    def set_default(self, code: str) -> Role:
        obj = self.get(code=code)
        if not obj.is_active:
            raise ValidationException("Only an active role can be set as default.")
        if not obj.is_default:
            before = self._snapshot(obj)
            Role.objects.exclude(pk=obj.pk).filter(is_default=True).update(
                is_default=False
            )
            obj.is_default = True
            obj.updated_by = self.user
            obj.save(update_fields=["is_default", "updated_by", "updated_at"])
            AuditService.log_set_default(
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
        role_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=role_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> list[dict]:
        return [
            {
                "code": r.code,
                "role": r.role,
                "is_default": r.is_default,
                "is_assignable": r.is_assignable,
                "is_leadership": r.is_leadership,
            }
            for r in selectors.get_role_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_role_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class RoleImportService(ImportService):
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
        role = (row.get("role") or "").strip()
        if not role:
            errors.append(
                {"row": row_num, "field": "role", "message": "Role name is required."}
            )
        elif len(role) > 100:
            errors.append(
                {
                    "row": row_num,
                    "field": "role",
                    "message": "Role name must be 100 characters or fewer.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        self.validate_csv_not_empty(content)
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"role"}
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
        role_svc = RoleService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            role = row["role"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")
            is_assignable_raw = (row.get("is_assignable") or "false").strip().lower()
            is_assignable = is_assignable_raw in ("true", "1", "yes")
            is_leadership_raw = (row.get("is_leadership") or "false").strip().lower()
            is_leadership = is_leadership_raw in ("true", "1", "yes")

            if selectors.role_exists(role):
                errors.append(
                    {
                        "row": row_num,
                        "field": "role",
                        "message": f"A role named '{role}' already exists.",
                    }
                )
                continue

            if not dry_run:
                role_svc.create(
                    role=role,
                    is_active=is_active,
                    is_assignable=is_assignable,
                    is_leadership=is_leadership,
                )

            created_rows.append({"row": row_num, "field": "role", "message": role})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class RoleExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "role": "Role Name",
        "is_active": "Active",
        "is_default": "Default",
        "is_assignable": "Assignable",
        "is_leadership": "Leadership",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "role",
        "is_active",
        "is_default",
        "is_assignable",
        "is_leadership",
        "created_at",
    ]
    EXPORT_FILENAME = "roles_export"
    EXPORT_MODULE_NAME = "Roles"

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

        qs = selectors.get_all_roles()
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
                qs = qs.filter(role__icontains=search)

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
